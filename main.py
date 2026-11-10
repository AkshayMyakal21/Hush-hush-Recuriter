import asyncio
import json
import os
from dotenv import load_dotenv
from api_integration.parser_api import parse_user, parse_search_results, parse_repos, parse_activity
from api_integration.github_api_client import GithubAPIClient
from scorer import calculate_range, calculate_github_score
from clustering import cluster_candidates, identify_strong_cluster, label_candidate
from database import create_tables, save_candidate, save_score, get_candidate_id, save_candidate_query, candidate_by_role
from classifier import predict_candidate, train_model, predict_confidence
from config import ROLE_QUERIES, build_queries
from notifier import notify_selected_candidates, SMTP_USER, SMTP_PASSWORD

load_dotenv()
token = os.environ.get("GITHUB_TOKEN")

async def fetch_candidate(client, username):
      user = await client.get_user(username)
      repos = await client.get_user_repos(username)
      events = await client.get_user_events(username)

      candidate = parse_user(user)

      if candidate is None:
            return None
      
      repo_stats = parse_repos(repos)

      candidate.total_stars = repo_stats["total_stars"]
      candidate.total_forks = repo_stats["total_forks"]
      candidate.top_language = repo_stats["top_language"]
      candidate.commit_count = parse_activity(events)

      return candidate
async def fetch_candidates_in_batches(client, usernames, batch_size = 10):
      valid_candidates = []
      usernames = list(usernames)

      for i in range (0, len(usernames), batch_size):
            batch = usernames[i:i + batch_size]
            tasks = [fetch_candidate(client, username) for username in batch]
            results = await asyncio.gather(*tasks, return_exceptions = True)

            for result in results:
                  if isinstance(result, Exception):
                        print(f"failed: {str(result)}")
                  elif result is None:
                        print("Organization account detected. Skipping...")
                  else:
                        valid_candidates.append(result)
            await asyncio.sleep(5)
            
      return valid_candidates

async def main():
      create_tables()


      role = input(f'Enter role {list(ROLE_QUERIES.keys())}: ')
      queries = build_queries(role)
      
      if not queries:
            print(f"Role {role} not found.\n Maybe try from these roles: {list(ROLE_QUERIES.keys())}")
            return

      async with GithubAPIClient(token = token) as client:
        
            search_task = [
                  client.search_users(query = query, limit = 5)
                  for query in queries
            ]
            search_results = await asyncio.gather(*search_task)
        
            username_to_query = {}
            for query, result in zip(queries, search_results):
                  for username in parse_search_results(result):
                        if username not in username_to_query:
                              username_to_query[username] = query

            candidates = await fetch_candidates_in_batches(client, username_to_query.keys())


            ranges = calculate_range(candidates)
            for candidate in candidates:
                  candidate.github_score = calculate_github_score(candidate, ranges)

            candidates.sort(key = lambda c: c.github_score, reverse = True)

            cluster_labels = cluster_candidates(candidates)
            strong_cluster = identify_strong_cluster(candidates, cluster_labels)
            candidates = label_candidate(candidates, cluster_labels, strong_cluster)

            for candidate in candidates:
                  if candidate.commit_count < 30:
                        candidate.is_selected = False

            for candidate in candidates:
                  save_candidate(candidate)
                  candidate_id = get_candidate_id(candidate.username)
                  save_score(candidate_id, candidate.github_score, candidate.is_selected)
                  save_candidate_query(candidate_id, role, username_to_query.get(candidate.username, role))

            train_model()
            predictions = []
            print("\nModel verdicts:")
            for candidate in candidates:
                  verdict = predict_candidate(candidate.followers, candidate.public_repos, candidate.total_stars, candidate.total_forks, candidate.commit_count)
                  #print(f"{candidate.username} - {verdict}")

                  confidence = predict_confidence(candidate.followers, candidate.public_repos, candidate.total_stars, candidate.total_forks, candidate.commit_count)
                  #print(f"{candidate.username} - {confidence}")

                  predictions.append((candidate.username, verdict, confidence))
            
            predictions.sort(key = lambda p: p[2], reverse = True)
            
            for username, verdict, confidence in predictions:
                  print(f"{username} - {verdict} - {confidence:.1f}%")

            print(f"Successfully fetched {len(candidates)} candidates")
            print("\nTop 5 candidates")
            for candidate in candidates[:5]:
                  print(f"{candidate.username} - {candidate.github_score}")
            print(f"Successfully fetched {len(candidates)} candidates")

            selected = [candidate for candidate in candidates if candidate.is_selected]
            print(f"\nK-Means selected {len(selected)} strong candidates:")
            for candidate in selected:
                  print(f"{candidate.username} - {candidate.github_score}")

            print(f"Saved {len(candidates)} candidates to the database")

            print(f"Found {len(username_to_query)} unique usernames")

            # Email a notification of the selected candidates (only if SMTP is configured).
            if SMTP_USER and SMTP_PASSWORD:
                  try:
                        selected_records = [
                              {
                                    "username": c.username,
                                    "profile_url": c.profile_url,
                                    "github_score": c.github_score,
                                    "top_language": c.top_language,
                                    "commit_count": c.commit_count,
                              }
                              for c in selected
                        ]
                        recipient = notify_selected_candidates(selected_records)
                        print(f"Sent selection notification to {recipient}")
                  except Exception as e:
                        print(f"Could not send notification email: {e}")
            else:
                  print("SMTP not configured; skipping email notification.")

asyncio.run(main())
