"""Maintenance analyzer — GitHub API integration for repository health."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from app.clients.github_client import GitHubClient
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DependencyMaintenanceResult:
    """Maintenance analysis result for a single dependency."""
    dependency_id: str
    last_commit_at: Optional[datetime] = None
    stars: Optional[int] = None
    is_archived: bool = False
    release_frequency_days: Optional[int] = None
    maintenance_score: Optional[int] = None
    status: str = "UNKNOWN"


class MaintenanceAnalyzer:
    """Analyzes dependency repository maintenance health via GitHub API."""

    def __init__(self):
        self.client = GitHubClient()

    async def analyze(
        self,
        dependencies: list[dict],
    ) -> list[DependencyMaintenanceResult]:
        """
        Analyze maintenance health for dependencies with GitHub repo URLs.

        Args:
            dependencies: List of dicts with keys: id, repo_url

        Returns:
            List of maintenance analysis results.
        """
        results = []

        for dep in dependencies:
            repo_url = dep.get("repo_url")
            dep_id = dep["id"]

            if not repo_url:
                results.append(DependencyMaintenanceResult(
                    dependency_id=dep_id,
                    status="UNKNOWN",
                ))
                continue

            parsed = GitHubClient.parse_github_url(repo_url)
            if not parsed:
                results.append(DependencyMaintenanceResult(
                    dependency_id=dep_id,
                    status="UNKNOWN",
                ))
                continue

            owner, repo = parsed

            try:
                info = await self.client.get_repo_info(owner, repo)

                score = self._calculate_score(
                    is_archived=info.is_archived,
                    last_commit_at=info.last_commit_at,
                    stars=info.stars,
                    release_frequency_days=info.release_frequency_days,
                )

                results.append(DependencyMaintenanceResult(
                    dependency_id=dep_id,
                    last_commit_at=info.last_commit_at,
                    stars=info.stars,
                    is_archived=info.is_archived,
                    release_frequency_days=info.release_frequency_days,
                    maintenance_score=score,
                    status=info.status,
                ))

            except Exception as e:
                logger.error(
                    "Maintenance analysis failed for dependency",
                    error=str(e), dep_id=dep_id, repo_url=repo_url,
                )
                results.append(DependencyMaintenanceResult(
                    dependency_id=dep_id,
                    status="UNKNOWN",
                ))

        return results

    def _calculate_score(
        self,
        is_archived: bool,
        last_commit_at: Optional[datetime],
        stars: Optional[int],
        release_frequency_days: Optional[int],
    ) -> int:
        """
        Calculate maintenance score (0-100, higher = healthier).
        Formula from spec Section 13.
        """
        score = 100

        if is_archived:
            return 0

        # Penalize stale repos
        if last_commit_at:
            now = datetime.now(timezone.utc)
            days_since = (now - last_commit_at).days

            if days_since > 730:
                score -= 50
            elif days_since > 365:
                score -= 25
            elif days_since > 180:
                score -= 10

        # Penalize low-star repos
        if stars is not None:
            if stars < 10:
                score -= 15
            elif stars < 100:
                score -= 5

        # Penalize infrequent releases
        if release_frequency_days is not None and release_frequency_days > 365:
            score -= 10

        return max(0, min(100, score))
