from fastapi.testclient import TestClient

from thb_input.api.v1.strip import get_strip_service
from thb_input.main import app
from thb_input.schemas.input import TextInputRequest
from thb_input.services.text_input import build_text_input_record
from thb_input.strip.service import StripService


class ApiFakeLLMClient:
    def complete_structured(self, prompt: object) -> object:
        return {
            "segments": [
                {
                    "text": "今天必须完成。",
                    "labels": ["demand", "deadline_expression"],
                }
            ],
        }


def test_strip_api_accepts_canonical_input() -> None:
    app.dependency_overrides[get_strip_service] = lambda: StripService(ApiFakeLLMClient())
    canonical_input = build_text_input_record(
        TextInputRequest(source_message="今天必须完成。")
    )

    try:
        response = TestClient(app).post(
            "/api/v1/strip",
            json=canonical_input.model_dump(mode="json"),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["segments"][0]["labels"] == [
        "demand",
        "deadline_expression",
    ]


def test_http_pipeline_input_then_strip() -> None:
    app.dependency_overrides[get_strip_service] = lambda: StripService(ApiFakeLLMClient())
    client = TestClient(app)

    try:
        input_response = client.post(
            "/api/v1/input/text",
            json={"source_message": "今天必须完成。"},
        )
        strip_response = client.post(
            "/api/v1/strip",
            json=input_response.json(),
        )
    finally:
        app.dependency_overrides.clear()

    assert input_response.status_code == 201
    assert strip_response.status_code == 200
    assert strip_response.json()["segments"][0]["text"] == "今天必须完成。"
