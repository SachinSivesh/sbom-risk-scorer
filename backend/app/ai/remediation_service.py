"""AI remediation service — generates natural-language summaries from risk reports."""

import json
from typing import Optional
from app.ai.prompts import SYSTEM_PROMPT, RETRY_SUFFIX
from app.clients.llm_client import LLMClient
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
        response_text = await self.client.generate(
            system_prompt=SYSTEM_PROMPT,
            user_message=report_json,
        )

        if response_text:
            parsed = self._parse_response(response_text)
            if parsed:
                parsed["model_used"] = "claude-sonnet-4-20250514"
                parsed["fallback_used"] = False
                return parsed

            # Retry once with stricter instructions
            logger.warning("First LLM response failed validation, retrying")
            response_text = await self.client.generate(
                system_prompt=SYSTEM_PROMPT + RETRY_SUFFIX,
                user_message=report_json,
            )

            if response_text:
                parsed = self._parse_response(response_text)
                if parsed:
                    parsed["model_used"] = "claude-sonnet-4-20250514"
                    parsed["fallback_used"] = False
                    return parsed

        # Fallback to deterministic template
        logger.warning("LLM failed, using deterministic fallback template")
        return self._generate_fallback(risk_report)

    def _parse_response(self, text: str) -> Optional[dict]:
        """Parse and validate the LLM JSON response."""
        try:
            # Strip markdown code fences if present
            cleaned = text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1])

            data = json.loads(cleaned)

            # Validate required fields
            if not isinstance(data.get("summary"), str):
                return None
            if not isinstance(data.get("top_actions"), list):
                return None

            # Validate each action
            for action in data["top_actions"]:
                if not all(k in action for k in ("title", "description", "priority")):
                    return None
                if action["priority"] not in ("HIGH", "MEDIUM", "LOW"):
                    return None

            # Cap to 3 actions
            data["top_actions"] = data["top_actions"][:3]

            return data

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("Failed to parse LLM response", error=str(e))
            return None

    def _generate_fallback(self, risk_report: dict) -> dict:
        """Generate a deterministic fallback summary from the risk report."""
        score = risk_report.get("overall_score", 0)
        category = risk_report.get("category", "LOW")
        vuln_sub = risk_report.get("vulnerability_subscore", 0)
        license_sub = risk_report.get("license_subscore", 0)
        maint_sub = risk_report.get("maintenance_subscore", 0)

        # Build summary
        summary = (
            f"This application has a {category} risk rating with an overall score of {score}/100. "
            f"The vulnerability risk score is {vuln_sub}/100, license compliance risk is {license_sub}/100, "
            f"and maintenance health risk is {maint_sub}/100."
        )

        # Build actions based on highest subscores
        actions = []
        sub_scores = [
            ("vulnerability", vuln_sub, "Review and remediate known vulnerabilities"),
            ("license", license_sub, "Review license compliance"),
            ("maintenance", maint_sub, "Evaluate dependency health and consider alternatives"),
        ]
        sub_scores.sort(key=lambda x: x[1], reverse=True)

        for name, sub_score, desc in sub_scores:
            if sub_score > 0 and len(actions) < 3:
                priority = "HIGH" if sub_score >= 50 else "MEDIUM" if sub_score >= 25 else "LOW"
                actions.append({
                    "title": f"Address {name} risks (score: {sub_score}/100)",
                    "description": desc,
                    "priority": priority,
                })

        # Extract top contributing deps from breakdown
        breakdown = risk_report.get("breakdown", {})
        top_deps = breakdown.get("top_contributing_dependencies", [])
        if top_deps and len(actions) < 3:
            dep = top_deps[0]
            actions.append({
                "title": f"Prioritize {dep.get('name', 'unknown')}@{dep.get('version', 'unknown')}",
                "description": f"This dependency has the highest weighted risk contribution ({dep.get('weighted_contribution', 0)}).",
                "priority": "HIGH",
            })

        return {
            "summary": summary,
            "top_actions": actions[:3],
            "fallback_used": True,
            "model_used": "deterministic-fallback",
        }

    def _no_risk_response(self) -> dict:
        """Response for zero-risk applications."""
        return {
            "summary": "No significant risks detected. This application's dependencies appear to be well-maintained, properly licensed, and free of known vulnerabilities.",
            "top_actions": [],
            "fallback_used": True,
            "model_used": "deterministic-fallback",
        }
