"""License analyzer — static rule evaluation against the conflict matrix."""

from dataclasses import dataclass, field
from app.models.license import evaluate_license_expression, find_license_conflicts
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DependencyLicenseResult:
    """License analysis result for a single dependency."""
    dependency_id: str
    license_id: str
    risk_level: str  # NONE | LOW | MEDIUM | HIGH
    conflicts: list[str] = field(default_factory=list)


class LicenseAnalyzer:
    """Analyzes dependency licenses for compatibility and risk."""

    def analyze(
        self,
        dependencies: list[dict],
    ) -> list[DependencyLicenseResult]:
        """
        Analyze license risk for a list of dependencies.

        Args:
            dependencies: List of dicts with keys: id, license_id

        Returns:
            List of license analysis results per dependency.
        """
        results = []
        all_license_ids = []

        for dep in dependencies:
            raw_license = dep.get("license_id")
            license_id, risk_level = evaluate_license_expression(raw_license)

            results.append(DependencyLicenseResult(
                dependency_id=dep["id"],
                license_id=license_id,
                risk_level=risk_level,
            ))
            all_license_ids.append(license_id)

        # Find cross-dependency conflicts
        conflicts = find_license_conflicts(all_license_ids)
        if conflicts:
            logger.info("License conflicts found", count=len(conflicts))
            # Add conflicts to all HIGH-risk dependencies
            for result in results:
                if result.risk_level == "HIGH":
                    result.conflicts = conflicts

        return results
