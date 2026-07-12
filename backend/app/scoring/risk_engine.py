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
    depth: int = 1  # NEW: depth in the dependency graph
    license_id: str = "UNKNOWN"
    vulnerabilities: list = field(default_factory=list)


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
        criticality: Optional[str] = None,
    ) -> RiskScoreResult:
        """
        Calculate the overall application risk score.

        Args:
            dependency_scores: List of per-dependency scores.
            criticality: Business criticality rating of the application.

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

        # Calculate sub-scores using a blend of Max Severity (40%) and Weighted Average Exposure (60%)
        # This prevents dilution while maintaining a realistic risk distribution
        
        # 1. Vulnerabilities
        v_scores_w = [(d.vuln_score, d.is_direct, getattr(d, 'depth', 1)) for d in dependency_scores]
        v_avg = self._weighted_average(v_scores_w)
        v_max = max((d.vuln_score for d in dependency_scores), default=0)
        vuln_subscore = v_max * 0.4 + v_avg * 0.6

        # 2. Licenses
        l_scores_w = [(d.license_score, d.is_direct, getattr(d, 'depth', 1)) for d in dependency_scores]
        l_avg = self._weighted_average(l_scores_w)
        l_max = max((d.license_score for d in dependency_scores), default=0)
        license_subscore = l_max * 0.4 + l_avg * 0.6

        # 3. Maintenance: only include deps with known scores
        maint_deps_all = [
            (100 - d.maintenance_score, d.is_direct, getattr(d, 'depth', 1))
            for d in dependency_scores
            if d.maintenance_score is not None
        ]
        
        maintenance_subscore = None
        if maint_deps_all:
            m_avg = self._weighted_average(maint_deps_all)
            m_max = max((100 - d.maintenance_score for d in dependency_scores if d.maintenance_score is not None), default=0)
            maintenance_subscore = m_max * 0.4 + m_avg * 0.6

        # Apply criticality multipliers: CRITICAL=1.5, HIGH=1.2, MEDIUM=1.0, LOW=0.7
        crit_multiplier = {"CRITICAL": 1.5, "HIGH": 1.2, "MEDIUM": 1.0, "LOW": 0.7}.get(criticality, 1.0)
        
        # Save base values before multiplier scaling
        vuln_subscore_base = vuln_subscore
        license_subscore_base = license_subscore
        maintenance_subscore_base = maintenance_subscore if maintenance_subscore is not None else 0
        
        vuln_subscore = min(100, round(vuln_subscore * crit_multiplier))
        license_subscore = min(100, round(license_subscore * crit_multiplier))
        if maintenance_subscore is not None:
            maintenance_subscore = min(100, round(maintenance_subscore * crit_multiplier))

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

        # Calculate base contributions before criticality mapping
        v_base = round(weights["vulnerability"] * vuln_subscore_base)
        l_base = round(weights["license"] * license_subscore_base)
        m_base = round(weights["maintenance"] * maintenance_subscore_base)
        crit_impact = overall - (v_base + l_base + m_base)

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

        # Evaluate compliance policies
        from app.scoring.policy_engine import PolicyEngine
        all_vulns = []
        for d in dependency_scores:
            all_vulns.extend(d.vulnerabilities)
        licenses_list = [d.license_id for d in dependency_scores]
        policy_eval = PolicyEngine.evaluate(
            overall_score=overall,
            criticality=criticality if criticality else "MEDIUM",
            vulnerabilities=all_vulns,
            licenses=licenses_list
        )

        return RiskScoreResult(
            overall_score=overall,
            category=category,
            vulnerability_subscore=round(vuln_subscore),
            license_subscore=round(license_subscore),
            maintenance_subscore=round(maintenance_subscore_final),
            breakdown={
                "weights_used": weights,
                "contributions": {
                    "vulnerability": v_base,
                    "license": l_base,
                    "maintenance": m_base,
                    "business_criticality": crit_impact
                },
                "policy_evaluation": policy_eval,
                "top_contributing_dependencies": [
                    {
                        "name": d.name,
                        "version": d.version,
                        "is_direct": d.is_direct,
                        "vuln_score": d.vuln_score,
                        "license_score": d.license_score,
                        "maintenance_score": d.maintenance_score,
                        "weighted_contribution": round(d.weighted_contribution, 2),
                        "depth": getattr(d, 'depth', 1),
                    }
                    for d in top_deps
                ],
                "confidence": round(confidence, 3),
                "total_dependencies": total_deps,
                "dependencies_with_complete_data": complete_deps,
                "criticality_multiplier_applied": crit_multiplier,
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
    def _weighted_average(scores_direct_depth: list[tuple[int, bool, int]]) -> float:
        """
        Weighted average: direct dependencies get 2x weight, transitive get 1x.
        Additionally, attenuate based on depth in the dependency graph.
        """
        if not scores_direct_depth:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for score, is_direct, depth in scores_direct_depth:
            # Base weight: direct gets 2.0, transitive gets 1.0
            base_w = 2.0 if is_direct else 1.0
            # Attenuation by depth: weight = base_w / depth
            w = base_w / max(1, depth)
            weighted_sum += score * w
            total_weight += w

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
