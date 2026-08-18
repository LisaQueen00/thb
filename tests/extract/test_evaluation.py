from tests.extract.helpers import empty_result

from thb_input.extract.acceptance import ACCEPTANCE_CASES
from thb_input.extract.evaluation import evaluate_result
from thb_input.extract.schemas import ExtractResult


def test_evaluator_reports_missing_expected_sections() -> None:
    case = ACCEPTANCE_CASES[0]
    evaluation = evaluate_result(ExtractResult.model_validate(empty_result()), case)
    assert evaluation.passed is False
    assert evaluation.missing_expected == {
        "claims",
        "requests",
        "time_constraints",
    }


def test_evaluator_rejects_risk_in_anti_overanalysis_case() -> None:
    payload = empty_result()
    payload["requests"] = [object()]
    payload["time_constraints"] = [object()]
    payload["conditions_and_consequences"] = [object()]
    payload["risks"] = [object()]
    case = ACCEPTANCE_CASES[-1]

    class ResultProjection:
        conflicts: list[object] = []

        def __init__(self) -> None:
            for field in case.expected_non_empty:
                setattr(self, field, [object()])
            self.risks = [object()]
            self.possible_intentions = []

    evaluation = evaluate_result(ResultProjection(), case)  # type: ignore[arg-type]
    assert evaluation.passed is False
    assert evaluation.unexpectedly_non_empty == {"risks"}


def test_evaluator_accepts_matching_projection() -> None:
    case = ACCEPTANCE_CASES[9]

    class ResultProjection:
        conflicts: list[object] = []
        risks: list[object] = []

        def __init__(self) -> None:
            for field in case.expected_non_empty:
                setattr(self, field, [object()])

    assert evaluate_result(ResultProjection(), case).passed is True  # type: ignore[arg-type]
