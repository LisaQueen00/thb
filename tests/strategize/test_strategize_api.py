from fastapi.testclient import TestClient
from tests.strategize.helpers import FakeLLM, make_request, strategy_result

from thb_input.api.v1.strategize import get_strategize_service
from thb_input.main import app
from thb_input.strategize.service import StrategizeService


def test_strategize_api_returns_valid_options() -> None:
    app.dependency_overrides[get_strategize_service] = lambda: StrategizeService(
        FakeLLM(strategy_result())
    )
    try:
        response = TestClient(app).post(
            "/api/v1/strategize",
            json=make_request().model_dump(mode="json"),
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["strategy_version"] == "0.1"
    assert len(response.json()["options"]) == 2


def test_strategize_api_maps_semantic_failure_to_422() -> None:
    payload = strategy_result(recommended="strategy_999")
    app.dependency_overrides[get_strategize_service] = lambda: StrategizeService(
        FakeLLM(payload), validation_retries=0
    )
    try:
        response = TestClient(app).post(
            "/api/v1/strategize",
            json=make_request().model_dump(mode="json"),
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "SEMANTIC_VALIDATION_FAILED"
