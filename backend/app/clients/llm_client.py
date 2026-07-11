"""LLM client for Google Gemini API."""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class TopAction(BaseModel):
    title: str = Field(description="Short title of the action")
    description: str = Field(description="Details of the remediation action")
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(description="Priority of the action")


class RemediationSummary(BaseModel):
    summary: str = Field(description="Natural-language remediation summary from the risk report")
    top_actions: List[TopAction] = Field(description="Top prioritized remediation actions (up to 3)")


class LLMClient:
    """Async client for Google Gemini API."""

    def __init__(self):
        self.settings = get_settings()

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1500,
    ) -> Optional[str]:
        """
        Generate a response from Gemini.

        Returns:
            Raw response text, or None on failure.
        """
        if not self.settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set, using deterministic fallback")
            logger.warning("Fallback is used")
            return None

        try:
            logger.info("Gemini request starts", model="gemini-3.5-flash")
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.settings.GEMINI_API_KEY)

            async with client.aio as aclient:
                response = await aclient.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        max_output_tokens=max_tokens,
                        response_mime_type="application/json",
                        response_schema=RemediationSummary,
                        thinking_config=types.ThinkingConfig(
                            thinking_budget=0
                        ),
                    ),
                )

            if response.parsed:
                logger.info("Gemini response succeeds", model="gemini-3.5-flash")
                return response.parsed

            logger.warning("Gemini returned empty response, using deterministic fallback")
            logger.warning("Fallback is used")
            return None

        except Exception as e:
            logger.error("Gemini request failed, using deterministic fallback", error=str(e))
            logger.warning("Fallback is used")
            return None

