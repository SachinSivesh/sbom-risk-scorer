import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.ai.remediation_service import RemediationService


@pytest.mark.asyncio
async def test_remediation_service_no_risk():
    service = RemediationService()
    report = {"overall_score": 0}
    res = await service.generate_summary(report)
    assert res["fallback_used"] is True
    assert "No significant software supply chain risks have been identified" in res["summary"]
    assert res["model_used"] == "deterministic-fallback"


@pytest.mark.asyncio
async def test_remediation_service_gemini_success():
    service = RemediationService()
    report = {
        "overall_score": 55,
        "category": "HIGH",
        "vulnerability_subscore": 60,
        "license_subscore": 30,
        "maintenance_subscore": 10,
    }

    from app.clients.llm_client import RemediationSummary, TopAction
    mock_llm_response = RemediationSummary(
        summary="AI generated summary highlighting vulnerability and maintenance risks.",
        top_actions=[
            TopAction(title="Upgrade library A", description="Fixes HIGH vulnerability", priority="HIGH"),
            TopAction(title="Check license of library B", description="Review details", priority="MEDIUM")
        ]
    )

    with patch.object(service.client, "generate", AsyncMock(return_value=mock_llm_response)) as mock_gen:
        res = await service.generate_summary(report)
        assert res["model_used"] == "gemini-3.5-flash"
        assert res["fallback_used"] is False
        assert "AI generated summary" in res["summary"]
        assert len(res["top_actions"]) == 2
        mock_gen.assert_called_once()


@pytest.mark.asyncio
async def test_remediation_service_gemini_api_failure_fallback():
    service = RemediationService()
    report = {
        "overall_score": 55,
        "category": "HIGH",
        "vulnerability_subscore": 60,
        "license_subscore": 30,
        "maintenance_subscore": 10,
    }

    # API returns None -> should fall back immediately after 1 call
    with patch.object(service.client, "generate", AsyncMock(return_value=None)) as mock_gen:
        res = await service.generate_summary(report)
        assert res["model_used"] == "deterministic-fallback"
        assert res["fallback_used"] is True
        assert "indicates a **HIGH** threat" in res["summary"]
        assert len(res["top_actions"]) > 0
        assert mock_gen.call_count == 1


@pytest.mark.asyncio
async def test_remediation_service_gemini_parse_failure_fallback():
    service = RemediationService()
    report = {
        "overall_score": 55,
        "category": "HIGH",
        "vulnerability_subscore": 60,
        "license_subscore": 30,
        "maintenance_subscore": 10,
    }

    # API returns invalid response type -> should retry once and then fall back (2 calls)
    with patch.object(service.client, "generate", AsyncMock(return_value="invalid response")) as mock_gen:
        res = await service.generate_summary(report)
        assert res["model_used"] == "deterministic-fallback"
        assert res["fallback_used"] is True
        assert "indicates a **HIGH** threat" in res["summary"]
        assert len(res["top_actions"]) > 0
        assert mock_gen.call_count == 2
