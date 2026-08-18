from fastapi.testclient import TestClient
from tests.extract.helpers import FakeLLM, empty_result, make_request

from thb_input.api.v1.extract import get_extract_service
from thb_input.extract.service import ExtractService
from thb_input.main import app


def test_extract_api_accepts_canonical_input_and_strip_result() -> None:
    app.dependency_overrides[get_extract_service] = lambda: ExtractService(
        FakeLLM(empty_result())
    )
    request = make_request()
    try:
        response = TestClient(app).post(
            "/api/v1/extract",
            json=request.model_dump(mode="json"),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["analysis_version"] == "0.1"
    assert response.json()["risks"] == []


def test_extract_api_rejects_untraceable_evidence() -> None:
    payload = empty_result()
    payload["claims"] = [
        {
            "claim_id": "claim_001",
            "content": "无法追溯的主张",
            "source": "other",
            "epistemic_status": "reported_by_other",
            "supporting_segments": ["seg_999"],
        }
    ]
    app.dependency_overrides[get_extract_service] = lambda: ExtractService(
        FakeLLM(payload), validation_retries=0
    )
    try:
        response = TestClient(app).post(
            "/api/v1/extract",
            json=make_request().model_dump(mode="json"),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "EVIDENCE_VALIDATION_FAILED"
