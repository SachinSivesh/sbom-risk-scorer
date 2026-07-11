"""Deterministic Risk Scoring Engine.

Combines vulnerability, license, and maintenance sub-scores into
a single explainable Application Risk Score (0-100).

This engine is fully deterministic — no randomness, no LLM involvement.
Same inputs always produce the same output.
"""

from dataclasses import dataclass, field
from typing import Optional


# Severity weights for vulnerability scoring (Section 14.1)
SEVERITY_WEIGHT = {
    "CRITICAL": 100,
    "HIGH": 75,
    "MEDIUM": 50,
    "LOW": 25,
    "UNKNOWN": 50,  # Conservative default
}

# License risk weights (Section 14.1)
LICENSE_WEIGHT = {
    "NONE": 0,
    "LOW": 30,
    "MEDIUM": 60,
    "HIGH": 90,
}

# Overall score weights (Section 14.3)
DEFAULT_WEIGHTS = {
    "vulnerability": 0.5,
    "license": 0.3,
    "maintenance": 0.2,
}


@dataclass
class DependencyScore:
    """Individual dependency's contribution to the risk score."""
    dependency_id: str
    name: str
    version: str
    is_direct: bool
    vuln_score: int = 0
    license_score: int = 0
    maintenance_score: Optional[int] = None  # None = unknown
    weighted_contribution: float = 0.0


@dataclass
class RiskScoreResult:
    """Complete risk score calculation result."""
    overall_score: int = 0
    category: str = "LOW"
    vulnerability_subscore: int = 0
    license_subscore: int = 0
    maintenance_subscore: int = 0
    breakdown: dict = field(default_factory=dict)


class RiskEngine:
    """Deterministic risk scoring engine."""

    def calculate(
        self,
        dependency_scores: list[DependencyScore],
    ) -> RiskScoreResult:
        """
        Calculate the overall application risk score.

        Args:
            dependency_scores: List of per-dependency scores.

        Returns:
            RiskScoreResult with overall score, category, and explainability breakdown.
        """
        if not dependency_scores:
            return RiskScoreResult(
                overall_score=0,
                category="LOW",
                vulnerability_subscore=0,
                license_subscore=0,
                maintenance_subscore=0,
                breakdown={
                    "weights_used": DEFAULT_WEIGHTS,
                    "top_contributing_dependencies": [],
                    "confidence": 1.0,
                    "note": "No dependencies found",
                },
            )

        # Calculate application-level sub-scores using weighted averages
        vuln_subscore = self._weighted_average(
            [(d.vuln_score, d.is_direct) for d in dependency_scores]
        )
        license_subscore = self._weighted_average(
            [(d.license_score, d.is_direct) for d in dependency_scores]
        )

        # Maintenance: only include deps with known scores
        maintenance_deps = [
            (100 - d.maintenance_score, d.is_direct)
            for d in dependency_scores
            if d.maintenance_score is not None
        ]

        maintenance_subscore = None
        if maintenance_deps:
            maintenance_subscore = self._weighted_average(maintenance_deps)

        # Re-normalize weights if maintenance is missing
        weights = dict(DEFAULT_WEIGHTS)
        if maintenance_subscore is None:
            total = weights["vulnerability"] + weights["license"]
            weights = {
                "vulnerability": weights["vulnerability"] / total,
                "license": weights["license"] / total,
                "maintenance": 0,
            }
            maintenance_subscore_final = 0
        else:
            maintenance_subscore_final = maintenance_subscore

        # Calculate overall score
        overall = round(
            weights["vulnerability"] * vuln_subscore +
            weights["license"] * license_subscore +
            weights["maintenance"] * maintenance_subscore_final
        )
        overall = max(0, min(100, overall))

        # Determine category
        category = self._get_category(overall)

        # Calculate per-dependency weighted contributions for explainability
        for dep in dependency_scores:
            m_score = (100 - dep.maintenance_score) if dep.maintenance_score is not None else 0
            dep.weighted_contribution = (
                weights["vulnerability"] * dep.vuln_score +
                weights["license"] * dep.license_score +
                weights["maintenance"] * m_score
            )

        # Top 5 contributing dependencies
        top_deps = sorted(
            dependency_scores,
            key=lambda d: d.weighted_contribution,
            reverse=True,
        )[:5]

        # Confidence = proportion of dependencies with complete data
        total_deps = len(dependency_scores)
        complete_deps = sum(
            1 for d in dependency_scores
            if d.maintenance_score is not None
        )
        confidence = complete_deps / total_deps if total_deps > 0 else 1.0

        return RiskScoreResult(
            overall_score=overall,
            category=category,
            vulnerability_subscore=round(vuln_subscore),
            license_subscore=round(license_subscore),
            maintenance_subscore=round(maintenance_subscore_final),
            breakdown={
                "weights_used": weights,
                "top_contributing_dependencies": [
                    {
                        "name": d.name,
                        "version": d.version,
                        "is_direct": d.is_direct,
                        "vuln_score": d.vuln_score,
                        "license_score": d.license_score,
                        "maintenance_score": d.maintenance_score,
                        "weighted_contribution": round(d.weighted_contribution, 2),
                    }
                    for d in top_deps
                ],
                "confidence": round(confidence, 3),
                "total_dependencies": total_deps,
                "dependencies_with_complete_data": complete_deps,
            },
        )

    @staticmethod
    def compute_vuln_score(vulnerabilities: list[dict]) -> int:
        """
        Compute vulnerability sub-score for a single dependency.
        Uses max severity (not sum) — one CRITICAL should not be diluted.
        """
        if not vulnerabilities:
            return 0

        max_score = 0
        for v in vulnerabilities:
            severity = v.get("severity", "UNKNOWN")
            weight = SEVERITY_WEIGHT.get(severity, 50)
            max_score = max(max_score, weight)

        return max_score

    @staticmethod
    def compute_license_score(risk_level: str) -> int:
        """Compute license sub-score for a single dependency."""
        return LICENSE_WEIGHT.get(risk_level, 60)

    @staticmethod
    def _weighted_average(scores_and_direct: list[tuple[int, bool]]) -> float:
        """
        Weighted average: direct dependencies get 2x weight, transitive get 1x.
        """
        if not scores_and_direct:
            return 0.0

        total_weight = 0
        weighted_sum = 0

        for score, is_direct in scores_and_direct:
            weight = 2 if is_direct else 1
            weighted_sum += score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    @staticmethod
    def _get_category(score: int) -> str:
        """Map score to risk category."""
        if score >= 75:
            return "CRITICAL"
        elif score >= 50:
            return "HIGH"
        elif score >= 25:
            return "MEDIUM"
        return "LOW"
