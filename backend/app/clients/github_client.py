"""GitHub REST API v3 client for maintenance analysis."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import httpx
from app.utils.cache import get_cache
from app.utils.logging import get_logger
from app.config import get_settings

logger = get_logger(__name__)

GITHUB_API_BASE = "https://api.github.com"


@dataclass
class GitHubRepoInfo:
    """Maintenance data extracted from GitHub API."""
    last_commit_at: Optional[datetime] = None
    stars: Optional[int] = None
    is_archived: bool = False
    release_frequency_days: Optional[int] = None
    status: str = "UNKNOWN"  # OK | REPO_NOT_FOUND | UNKNOWN | RATE_LIMITED


class GitHubClient:
    """Async client for the GitHub REST API v3."""

    def __init__(self):
        self.cache = get_cache()
        self.settings = get_settings()
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "SBOM-Risk-Scorer/1.0",
        }
        if self.settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"Bearer {self.settings.GITHUB_TOKEN}"

    async def get_repo_info(self, owner: str, repo: str) -> GitHubRepoInfo:
        """
        Fetch repository maintenance information.

        Args:
            owner: GitHub repository owner
            repo: GitHub repository name

        Returns:
            GitHubRepoInfo with maintenance signals.
        """
        cache_key = f"github:{owner}/{repo}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            if cached.get("last_commit_at"):
                cached["last_commit_at"] = datetime.fromisoformat(cached["last_commit_at"])
            return GitHubRepoInfo(**cached)

        info = GitHubRepoInfo()

        async with httpx.AsyncClient(timeout=15.0) as client:
            # Fetch repo metadata
            try:
                response = await client.get(
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
                    headers=self.headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    info.stars = data.get("stargazers_count", 0)
                    info.is_archived = data.get("archived", False)
                    info.status = "OK"

                    # Parse pushed_at as last commit indicator
                    pushed_at = data.get("pushed_at")
                    if pushed_at:
                        info.last_commit_at = datetime.fromisoformat(
                            pushed_at.replace("Z", "+00:00")
                        )

                elif response.status_code == 404:
                    info.status = "REPO_NOT_FOUND"
                    await self._cache_result(cache_key, info)
                    return info
                elif response.status_code == 403:
                    # Rate limited
                    info.status = "RATE_LIMITED"
                    logger.warning("GitHub API rate limited", owner=owner, repo=repo)
                    return info
                else:
                    info.status = "UNKNOWN"
                    return info

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                logger.warning("GitHub API connection error", error=str(e), owner=owner, repo=repo)
                info.status = "UNKNOWN"
                return info

            # Fetch recent releases for frequency calculation
            try:
                response = await client.get(
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo}/releases",
                    headers=self.headers,
                    params={"per_page": 5},
                )

                if response.status_code == 200:
                    releases = response.json()
                    info.release_frequency_days = self._calculate_release_frequency(releases)

            except Exception as e:
                logger.warning("Failed to fetch releases", error=str(e))

        # Cache the result
        await self._cache_result(cache_key, info)
        return info

    async def _cache_result(self, cache_key: str, info: GitHubRepoInfo) -> None:
        """Cache a GitHubRepoInfo result."""
        cache_data = {
            "last_commit_at": info.last_commit_at.isoformat() if info.last_commit_at else None,
            "stars": info.stars,
            "is_archived": info.is_archived,
            "release_frequency_days": info.release_frequency_days,
            "status": info.status,
        }
        await self.cache.set(cache_key, cache_data, ttl=self.settings.GITHUB_CACHE_TTL)

    def _calculate_release_frequency(self, releases: list[dict]) -> Optional[int]:
        """Calculate average days between releases."""
        if len(releases) < 2:
            return None

        dates = []
        for rel in releases:
            published = rel.get("published_at")
            if published:
                dates.append(datetime.fromisoformat(published.replace("Z", "+00:00")))

        if len(dates) < 2:
            return None

        dates.sort(reverse=True)
        total_days = 0
        for i in range(len(dates) - 1):
            delta = (dates[i] - dates[i + 1]).days
            total_days += delta

        return total_days // (len(dates) - 1)

    @staticmethod
    def parse_github_url(url: str) -> Optional[tuple[str, str]]:
        """
        Extract owner and repo from a GitHub URL.

        Returns:
            Tuple of (owner, repo) or None if not a valid GitHub URL.
        """
        if not url or "github.com" not in url:
            return None

        url = url.rstrip("/")
        if url.endswith(".git"):
            url = url[:-4]

        parts = url.split("github.com/")
        if len(parts) < 2:
            return None

        path_parts = parts[1].split("/")
        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo = path_parts[1]
            # Clean up repo name (remove query params, fragments)
            repo = repo.split("?")[0].split("#")[0]
            return owner, repo

        return None
