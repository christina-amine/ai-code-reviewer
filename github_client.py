"""
GitHub API Client Wrapper
Handles OAuth authentication and PR analysis
"""

from github import Github, GithubException
from config import settings
from typing import Optional, List, Dict, Any
import re


class GitHubClient:
    """Wrapper around PyGithub for secure GitHub interactions"""

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize GitHub client with optional access token.

        Args:
            access_token: OAuth token from GitHub. If None, uses public API (limited).
        """
        self.access_token = access_token
        self.client = Github(access_token) if access_token else Github()

    @staticmethod
    def parse_pr_url(pr_url: str) -> tuple:
        """
        Parse GitHub PR URL to extract owner, repo, and PR number.

        Args:
            pr_url: URL like "https://github.com/owner/repo/pull/123"

        Returns:
            Tuple of (owner, repo, pr_number)

        Raises:
            ValueError: If URL format is invalid
        """
        pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.search(pattern, pr_url)

        if not match:
            raise ValueError(
                f"Invalid GitHub PR URL: {pr_url}. "
                f"Expected format: https://github.com/owner/repo/pull/123"
            )

        owner, repo, pr_num = match.groups()
        return owner, repo, int(pr_num)

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """
        Fetch changed files from a pull request.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            List of dicts with file info and changes:
            [
                {
                    "filename": "src/main.py",
                    "patch": "+new line\n-old line",
                    "additions": 5,
                    "deletions": 2,
                    "status": "modified"
                },
                ...
            ]

        Raises:
            GithubException: If PR not found or access denied
        """
        try:
            repository = self.client.get_repo(f"{owner}/{repo}")
            pull = repository.get_pull(pr_number)

            files_info = []
            for file in pull.get_files():
                files_info.append({
                    "filename": file.filename,
                    "patch": file.patch or "",
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "status": file.status,
                    "changes": file.changes,
                })

            return files_info

        except GithubException as e:
            raise ValueError(
                f"Failed to fetch PR: {e.data.get('message', str(e))}"
            )

    def get_pr_details(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """
        Fetch PR metadata (title, description, author, etc).

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            Dict with PR details
        """
        try:
            repository = self.client.get_repo(f"{owner}/{repo}")
            pull = repository.get_pull(pr_number)

            return {
                "title": pull.title,
                "description": pull.body or "",
                "author": pull.user.login,
                "created_at": pull.created_at.isoformat(),
                "updated_at": pull.updated_at.isoformat(),
                "state": pull.state,
                "additions": pull.additions,
                "deletions": pull.deletions,
                "changed_files": pull.changed_files,
            }

        except GithubException as e:
            raise ValueError(f"Failed to fetch PR details: {e}")

    def get_repo_languages(self, owner: str, repo: str) -> Dict[str, float]:
        """
        Get programming languages used in repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dict of language -> percentage
        """
        try:
            repository = self.client.get_repo(f"{owner}/{repo}")
            return repository.get_languages()
        except GithubException as e:
            return {}

    def validate_token(self) -> bool:
        """Check if the access token is valid."""
        try:
            self.client.get_user()
            return True
        except GithubException:
            return False


# Convenience functions for agent tools

def fetch_pr_for_review(pr_url: str, access_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch a PR and its files for code review.

    Args:
        pr_url: GitHub PR URL
        access_token: OAuth token

    Returns:
        Dict with PR details and file changes
    """
    client = GitHubClient(access_token)
    owner, repo, pr_number = client.parse_pr_url(pr_url)

    pr_details = client.get_pr_details(owner, repo, pr_number)
    pr_files = client.get_pr_files(owner, repo, pr_number)
    languages = client.get_repo_languages(owner, repo)

    return {
        "pr": pr_details,
        "files": pr_files,
        "languages": languages,
    }
