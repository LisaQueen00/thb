from dataclasses import dataclass

from thb_input.strip.schemas import StripResult
from thb_input.strip.taxonomy import CommunicationLabel


@dataclass(frozen=True)
class LabelExpectation:
    required: frozenset[CommunicationLabel]
    allowed: frozenset[CommunicationLabel]
    forbidden: frozenset[CommunicationLabel] = frozenset()
    required_any: tuple[frozenset[CommunicationLabel], ...] = ()


@dataclass(frozen=True)
class LabelEvaluation:
    passed: bool
    detected: frozenset[CommunicationLabel]
    missing_required: frozenset[CommunicationLabel]
    unexpected: frozenset[CommunicationLabel]
    forbidden_detected: frozenset[CommunicationLabel]
    missing_required_any: tuple[frozenset[CommunicationLabel], ...]


def evaluate_labels(
    result: StripResult, expectation: LabelExpectation
) -> LabelEvaluation:
    detected = frozenset(result.summary.detected_labels)
    missing_required = expectation.required - detected
    unexpected = detected - expectation.allowed
    forbidden_detected = detected & expectation.forbidden
    missing_required_any = tuple(
        group for group in expectation.required_any if not (detected & group)
    )
    return LabelEvaluation(
        passed=not (
            missing_required
            or unexpected
            or forbidden_detected
            or missing_required_any
        ),
        detected=detected,
        missing_required=missing_required,
        unexpected=unexpected,
        forbidden_detected=forbidden_detected,
        missing_required_any=missing_required_any,
    )
