from fastapi.testclient import TestClient
from tests.output.helpers import make_output_request

from thb_input.main import app


def test_output_api_returns_complete_final_view() -> None:
    response = TestClient(app).post(
        "/api/v1/output",
        json=make_output_request().model_dump(mode="json"),
    )
    assert response.status_code == 200
    assert response.json()["output_version"] == "0.1"
    assert response.json()["reply"]["copyable"] is True


def test_output_api_rejects_cross_stage_mismatch() -> None:
    payload = make_output_request().model_dump(mode="json")
    payload["respond_result"]["strategy_option_id"] = "strategy_999"
    response = TestClient(app).post("/api/v1/output", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INPUT_CONTRACT_MISMATCH"
