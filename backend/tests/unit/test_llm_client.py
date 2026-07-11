import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.clients.llm_client import LLMClient, RemediationSummary
from app.config import Settings


@pytest.mark.asyncio
async def test_llm_client_missing_key():
    # Test client when GEMINI_API_KEY is not configured
    settings = Settings(GEMINI_API_KEY="")
    with patch("app.clients.llm_client.get_settings", return_value=settings):
        client = LLMClient()
        result = await client.generate("system prompt", "user message")
        assert result is None


@pytest.mark.asyncio
async def test_llm_client_successful_response():
    # Test client when GEMINI_API_KEY is configured and request succeeds
    settings = Settings(GEMINI_API_KEY="test_key")
    with patch("app.clients.llm_client.get_settings", return_value=settings):
        # Mock google-genai client and generate_content
        mock_response = MagicMock()
        mock_response.parsed = RemediationSummary(
            summary="Mocked remediation response",
            top_actions=[]
        )

        mock_client = MagicMock()
        mock_aio_client = MagicMock()
        mock_client.aio.__aenter__ = AsyncMock(return_value=mock_aio_client)
        mock_aio_client.models.generate_content = AsyncMock(return_value=mock_response)

        with patch("google.genai.Client", return_value=mock_client):
            client = LLMClient()
            result = await client.generate("system prompt", "user message")
            assert result == mock_response.parsed
            mock_aio_client.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_llm_client_failure_fallback():
    # Test client when API call raises an exception
    settings = Settings(GEMINI_API_KEY="test_key")
    with patch("app.clients.llm_client.get_settings", return_value=settings):
        mock_client = MagicMock()
        mock_aio_client = MagicMock()
        mock_client.aio.__aenter__ = AsyncMock(return_value=mock_aio_client)
        mock_aio_client.models.generate_content = AsyncMock(side_effect=Exception("API Error"))

        with patch("google.genai.Client", return_value=mock_client):
            client = LLMClient()
            result = await client.generate("system prompt", "user message")
            assert result is None
