from dataclasses import dataclass
from typing import Optional


@dataclass
class Candidate:
    username: str
    followers: int
    profile_url: str
    public_repos: int
    total_stars: int = 0
    total_forks: int = 0
    commit_count: int = 0
    top_language: Optional[str] = None
    github_score: float = 0
    is_selected: bool = False
