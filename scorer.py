def calculate_range(candidates):
    return {
        "stars" : {
            "min" : min(c.total_stars for c in candidates),
            "max" : max(c.total_stars for c in candidates)
        },

        "forks" : {
            "min" : min(c.total_forks for c in candidates),
            "max" : max(c.total_forks for c in candidates)
        },

        "followers" : {
            "min" : min(c.followers for c in candidates),
            "max" : max(c.followers for c in candidates)
        },

        "repos" : {
            "min" : min(c.public_repos for c in candidates),
            "max" : max(c.public_repos for c in candidates)
        },

        "commit_count" : {
            "min" : min(c.commit_count for c in candidates),
            "max" : max(c.commit_count for c in candidates)
        }
    }

def normalize(value, min_value, max_value):
    if max_value == min_value:
        return 0
    return (value - min_value) / (max_value - min_value)

def calculate_github_score(candidate, ranges):
    stars_normalized = normalize(candidate.total_stars, ranges["stars"]["min"], ranges["stars"]["max"])
    forks_normalized = normalize(candidate.total_forks, ranges["forks"]["min"], ranges["forks"]["max"])
    followers_normalized = normalize(candidate.followers, ranges["followers"]["min"], ranges["followers"]["max"])
    repos_normalized = normalize(candidate.public_repos, ranges["repos"]["min"], ranges["repos"]["max"])
    commit_count_normalized = normalize(candidate.commit_count, ranges["commit_count"]["min"], ranges["commit_count"]["max"])

    score = (
        stars_normalized * 0.25 +
        forks_normalized * 0.15 +
        followers_normalized * 0.15 +
        repos_normalized * 0.15 +
        commit_count_normalized * 0.30
    )

    return round(score, 4)