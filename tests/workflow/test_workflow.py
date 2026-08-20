from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from tests.extract.helpers import empty_result, make_request

from thb import THBResult, THBState, THBWorkflow, WorkflowError
from thb_input.api.v1.thb import get_workflow, to_public_response
from thb_input.extract.schemas import ExtractResult
from thb_input.main import app
from thb_input.meaning import MeaningResult


@dataclass
class SpyService:
    name: str
    result: object
    calls: list[str]

    def process(self, request: object) -> object:
        self.calls.append(self.name)
        return self.result


def make_workflow() -> tuple[THBWorkflow, list[str]]:
    calls: list[str] = []
    upstream = make_request("Please confirm the document.")
    extract = ExtractResult.model_validate(empty_result("A document needs confirmation."))

    def input_service(request: object) -> object:
        calls.append("input")
        return upstream.canonical_input

    workflow = THBWorkflow(
        input_service=input_service,
        strip_service=SpyService("strip", upstream.strip_result, calls),
        extract_service=SpyService("extract", extract, calls),
        meaning_service=SpyService(
            "meaning", MeaningResult(meaning=extract.event_summary), calls
        ),
    )
    return workflow, calls


def test_run_executes_only_meaning_chain() -> None:
    workflow, calls = make_workflow()

    result = workflow.run("Please confirm the document.")

    assert result == MeaningResult(meaning="A document needs confirmation.")
    assert calls == ["input", "strip", "extract", "meaning"]


def test_extract_failure_stops_before_meaning() -> None:
    workflow, calls = make_workflow()

    class Failure:
        def process(self, request: object) -> object:
            calls.append("extract")
            raise ValueError("invalid extraction")

    workflow.extract_service = Failure()
    with pytest.raises(WorkflowError) as captured:
        workflow.run("Please confirm the document.")

    assert captured.value.code == "EXTRACT_FAILED"
    assert captured.value.stage == "extract"
    assert calls == ["input", "strip", "extract"]


def test_http_adapter_returns_only_unchanged_meaning() -> None:
    workflow, calls = make_workflow()
    app.dependency_overrides[get_workflow] = lambda: workflow
    try:
        response = TestClient(app).post(
            "/api/v1/thb", json={"source_message": "Please confirm the document."}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"meaning": "A document needs confirmation."}
    assert calls == ["input", "strip", "extract", "meaning"]


def test_removed_request_fields_are_rejected() -> None:
    response = TestClient(app).post(
        "/api/v1/thb",
        json={"source_message": "Hello", "user_goal": "write a reply"},
    )
    assert response.status_code == 422


def test_public_projection_is_deterministic() -> None:
    result = MeaningResult(meaning="Keep this exact text.")
    assert to_public_response(result).model_dump() == {"meaning": result.meaning}


def test_workflow_error_shape_is_preserved() -> None:
    class FailedWorkflow:
        def run(self, source_message: str, context: str | None) -> None:
            raise WorkflowError("EXTRACT_FAILED", "extract", "bad extraction", THBState())

    app.dependency_overrides[get_workflow] = FailedWorkflow
    try:
        response = TestClient(app).post(
            "/api/v1/thb", json={"source_message": "Hello"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json() == {
        "detail": {
            "code": "EXTRACT_FAILED",
            "stage": "extract",
            "message": "bad extraction",
        }
    }


def test_public_contract_imports() -> None:
    assert THBWorkflow is not None
    assert THBResult is MeaningResult
