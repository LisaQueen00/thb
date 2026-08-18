from dataclasses import dataclass

from thb_input.strategize.acceptance import StrategizeAcceptanceCase
from thb_input.strategize.schemas import StrategizeResult, StrategyType


@dataclass(frozen=True)
class StrategizeEvaluation:
    passed: bool
    missing_types: frozenset[StrategyType]
    forbidden_types: frozenset[StrategyType]
    missing_required_user_input: bool


def evaluate_result(
    result: StrategizeResult, case: StrategizeAcceptanceCase
) -> StrategizeEvaluation:
    actual_types = {option.strategy_type for option in result.options}
    missing = case.required_types - actual_types
    forbidden = case.forbidden_types & actual_types
    missing_user_input = case.requires_user_input and not result.required_user_input
    return StrategizeEvaluation(
        passed=not missing and not forbidden and not missing_user_input,
        missing_types=frozenset(missing),
        forbidden_types=frozenset(forbidden),
        missing_required_user_input=missing_user_input,
    )
