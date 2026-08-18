from fastapi.testclient import TestClient
from tests.respond.helpers import FakeLLM, make_request, result

from thb_input.api.v1.respond import get_respond_service
from thb_input.main import app
from thb_input.respond.service import RespondService


def test_respond_api_returns_ready_to_send_reply() -> None:
    app.dependency_overrides[get_respond_service] = lambda: RespondService(FakeLLM(result()))
    try:
        response = TestClient(app).post(
            "/api/v1/respond", json=make_request().model_dump(mode="json")
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["reply"] == "目前还在处理中，有进展我会同步。"


def test_respond_api_maps_constraint_failure_to_422() -> None:
    app.dependency_overrides[get_respond_service] = lambda: RespondService(
        FakeLLM(result("收到。")), validation_retries=0
    )
    try:
        response = TestClient(app).post(
            "/api/v1/respond", json=make_request().model_dump(mode="json")
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "CONSTRAINT_VALIDATION_FAILED"
