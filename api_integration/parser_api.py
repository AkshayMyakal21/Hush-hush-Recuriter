from models import Candidate
from collections import Counter
from datetime import datetime, timedelta, timezone

def parse_user(user_data):

    if user_data["type"] != "User":
        return None

    username = user_data['login'].lower()
    bot_keywords = ["bot", "automation", "ci-", "robot", "sdk"]
    if any(keyword in username for keyword in bot_keywords):
        return None

    return Candidate(
        username = user_data["login"],
        followers = user_data["followers"],
        profile_url = user_data["html_url"],
        public_repos = user_data["public_repos"]
    )

def parse_search_results(search_results):

    return [
        item["login"]
        for item in search_results["items"]
    ]

def parse_repos(repos_data):
    total_stars = sum(repo["stargazers_count"] for repo in repos_data)
    total_forks = sum(repo["forks_count"] for repo in repos_data)

    languages = [
        repo['language']
        for repo in repos_data
        if repo['language'] is not None
    ]

    top_language = Counter(languages).most_common(1)[0][0] if languages else None

    return {
        "total_stars": total_stars,
        "total_forks": total_forks,
        "top_language": top_language
    }

def parse_activity(events_data):
    count = 0
    deadline = datetime.now(tz=timezone.utc) - timedelta(days=90)
    for event in events_data:
        created = datetime.fromisoformat(event["created_at"].replace('Z', "+00:00"))
        if created > deadline:
            count += 1

    return count