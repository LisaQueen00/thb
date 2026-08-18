from dataclasses import dataclass

from thb_input.extract.acceptance import ExtractAcceptanceCase
from thb_input.extract.schemas import ExtractResult


@dataclass(frozen=True)
class ExtractEvaluation:
    passed: bool
    missing_expected: frozenset[str]
    unexpectedly_non_empty: frozenset[str]
    resolved_expected_conflicts: bool


def evaluate_result(
    result: ExtractResult, case: ExtractAcceptanceCase
) -> ExtractEvaluation:
    missing = frozenset(
        field for field in case.expected_non_empty if not getattr(result, field)
    )
    unexpected = frozenset(
        field for field in case.expected_empty if getattr(result, field)
    )
    resolved_expected_conflicts = "conflicts" in case.expected_non_empty and any(
        conflict.resolution != "unresolved" for conflict in result.conflicts
    )
    return ExtractEvaluation(
        passed=not missing and not unexpected and not resolved_expected_conflicts,
        missing_expected=missing,
        unexpectedly_non_empty=unexpected,
        resolved_expected_conflicts=resolved_expected_conflicts,
    )
