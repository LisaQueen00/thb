from tests.strategize.helpers import option, strategy_result

from thb_input.strategize.acceptance import ACCEPTANCE_CASES
from thb_input.strategize.evaluation import evaluate_result
from thb_input.strategize.schemas import StrategizeResult


def test_evaluator_accepts_required_strategy_types() -> None:
    result = StrategizeResult.model_validate(
        strategy_result(
            options=[
                option("strategy_001", "progress"),
                option("strategy_002", "clarify"),
            ]
        )
    )
    assert evaluate_result(result, ACCEPTANCE_CASES[0]).passed is True


def test_evaluator_reports_missing_and_forbidden_types() -> None:
    result = StrategizeResult.model_validate(
        strategy_result(
            options=[
                option("strategy_001", "boundary"),
                option("strategy_002", "clarify"),
            ]
        )
    )
    evaluation = evaluate_result(result, ACCEPTANCE_CASES[0])
    assert evaluation.passed is False
    assert {item.value for item in evaluation.missing_types} == {"progress"}
    assert {item.value for item in evaluation.forbidden_types} == {"boundary"}


def test_evaluator_requires_blocking_user_input() -> None:
    result = StrategizeResult.model_validate(strategy_result())
    evaluation = evaluate_result(result, ACCEPTANCE_CASES[7])
    assert evaluation.missing_required_user_input is True
