"""AI remediation service — generates natural-language summaries from risk reports."""

import json
from typing import Optional
from app.ai.prompts import SYSTEM_PROMPT, RETRY_SUFFIX
from app.clients.llm_client import LLMClient, RemediationSummary
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RemediationService:
    """Generates AI-powered remediation summaries from risk report data."""

    def __init__(self):
        self.client = LLMClient()

    async def generate_summary(
        self,
        risk_report: dict,
    ) -> dict:
        """
        Generate an AI remediation summary from a risk report.

        Args:
            risk_report: The complete risk report dict (never raw SBOM).

        Returns:
            Dict with keys: summary, top_actions, fallback_used, model_used
        """
        # Skip AI for zero findings
        if risk_report.get("overall_score", 0) == 0:
            return self._no_risk_response()

        report_json = json.dumps(risk_report, default=str, indent=2)

        # First attempt
        parsed_obj = await self.client.generate(
            system_prompt=SYSTEM_PROMPT,
            user_message=report_json,
        )

        if parsed_obj is None:
            # Fallback immediately
            logger.warning("LLM failed, using deterministic fallback template")
            logger.warning("Fallback is used")
            return self._generate_fallback(risk_report)

        if isinstance(parsed_obj, RemediationSummary):
            parsed = parsed_obj.model_dump()
            parsed["top_actions"] = parsed["top_actions"][:3]
            parsed["model_used"] = "gemini-3.5-flash"
            parsed["fallback_used"] = False
            return parsed

        # Retry once with stricter instructions
        logger.warning("First LLM response failed validation, retrying")
        parsed_obj = await self.client.generate(
            system_prompt=SYSTEM_PROMPT + RETRY_SUFFIX,
            user_message=report_json,
        )

        if isinstance(parsed_obj, RemediationSummary):
            parsed = parsed_obj.model_dump()
            parsed["top_actions"] = parsed["top_actions"][:3]
            parsed["model_used"] = "gemini-3.5-flash"
            parsed["fallback_used"] = False
            return parsed

        # Fallback to deterministic template
        logger.warning("LLM failed, using deterministic fallback template")
        logger.warning("Fallback is used")
        return self._generate_fallback(risk_report)

    def _generate_fallback(self, risk_report: dict) -> dict:
        """Generate a deterministic fallback summary from the risk report."""
        score = risk_report.get("overall_score", 0)
        category = risk_report.get("category", "LOW")
        vuln_sub = risk_report.get("vulnerability_subscore", 0)
        license_sub = risk_report.get("license_subscore", 0)
        maint_sub = risk_report.get("maintenance_subscore", 0)

        app_info = risk_report.get("application", {})
        app_name = app_info.get("name", "Target Application")
        crit = app_info.get("criticality", "MEDIUM")
        lic_model = app_info.get("license_model", "proprietary")

        # Build actions based on highest subscores
        actions = []
        sub_scores = [
            ("vulnerability", vuln_sub, "Prioritize dependency patching and vulnerability remediation across critical exposure paths."),
            ("license", license_sub, f"Audit license matrix for viral compliance concerns against the proprietary baseline."),
            ("maintenance", maint_sub, "Decommission archived or deprecated libraries to prevent technical debt accumulation."),
        ]
        sub_scores.sort(key=lambda x: x[1], reverse=True)

        for name, sub_score, desc in sub_scores:
            if sub_score > 0 and len(actions) < 3:
                priority = "HIGH" if sub_score >= 50 else "MEDIUM" if sub_score >= 25 else "LOW"
                actions.append({
                    "title": f"Mitigate {name} threat vector",
                    "description": desc,
                    "priority": priority,
                })

        # Structured markdown consultant summary
        summary = f"""### EXECUTIVE SUMMARY
The Software Supply Chain review of **{app_name}** indicates a **{category}** threat exposure posture. This assessment correlates open-source vulnerabilities, package license obligations, and codebase upkeep metrics, scaled against a **{crit}** criticality business rating.

---

### THREAT & ATTACK SURFACE ANALYSIS
* **Vulnerability Vectors**: A security score of **{vuln_sub}/100** indicates exposure to known vulnerabilities. These dependencies form active entry paths that must be insulated.
* **Component Aging & Maintenance**: The maintenance score of **{maint_sub}/100** points to unmaintained or deprecated libraries within the dependency tree.

---

### REGULATORY & COMPLIANCE IMPACT
The system is governed under a **{lic_model}** model. License subscore of **{license_sub}/100** identifies potential compliance issues with copyleft or viral licenses. A thorough licensing audit is advised to clear liability concerns.
"""

        return {
            "summary": summary,
            "top_actions": actions[:3],
            "fallback_used": True,
            "model_used": "deterministic-fallback",
        }

    def _no_risk_response(self) -> dict:
        """Response for zero-risk applications."""
        return {
            "summary": "### EXECUTIVE SUMMARY\nNo significant software supply chain risks have been identified. The application's dependencies are verified to be fully maintained, properly licensed, and free of known vulnerabilities.",
            "top_actions": [],
            "fallback_used": True,
            "model_used": "deterministic-fallback",
        }
