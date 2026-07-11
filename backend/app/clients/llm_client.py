"""LLM client for Anthropic Claude API."""

import json
from typing import Optional
from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Async client for Anthropic Claude API."""

    def __init__(self):
        self.settings = get_settings()

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1500,
    ) -> Optional[str]:
        """
        Generate a response from Claude.

        Returns:
            Raw response text, or None on failure.
        """
        if not self.settings.ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY not set, skipping LLM call")
            return None

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.settings.ANTHROPIC_API_KEY)

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ],
            )

            if message.content and len(message.content) > 0:
                return message.content[0].text

            return None

        except Exception as e:
            logger.error("LLM generation failed", error=str(e))
            return None
