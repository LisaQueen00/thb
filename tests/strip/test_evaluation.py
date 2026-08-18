from thb_input.strip.evaluation import LabelExpectation, evaluate_labels
from thb_input.strip.schemas import StripResult
from thb_input.strip.taxonomy import CommunicationLabel


def result_with_labels(*labels: CommunicationLabel) -> StripResult:
    return StripResult.model_validate(
        {
            "strip_version": "0.1",
            "segments": [
                {"segment_id": "seg_001", "text": "测试。", "labels": labels}
            ],
            "summary": {
                "detected_labels": labels,
                "contains_implicit_language": False,
                "contains_pressure_language": False,
                "contains_evaluative_language": False,
            },
        }
    )


def test_label_evaluation_passes_required_and_allowed_labels() -> None:
    result = result_with_labels(
        CommunicationLabel.STATEMENT,
        CommunicationLabel.REQUEST,
    )
    expectation = LabelExpectation(
        required=frozenset({CommunicationLabel.REQUEST}),
        allowed=frozenset(
            {CommunicationLabel.STATEMENT, CommunicationLabel.REQUEST}
        ),
        forbidden=frozenset({CommunicationLabel.PERSONAL_EVALUATION}),
    )

    assert evaluate_labels(result, expectation).passed is True


def test_label_evaluation_reports_missing_unexpected_and_forbidden() -> None:
    result = result_with_labels(
        CommunicationLabel.STATEMENT,
        CommunicationLabel.PERSONAL_EVALUATION,
    )
    expectation = LabelExpectation(
        required=frozenset({CommunicationLabel.REQUEST}),
        allowed=frozenset({CommunicationLabel.STATEMENT}),
        forbidden=frozenset({CommunicationLabel.PERSONAL_EVALUATION}),
    )

    evaluation = evaluate_labels(result, expectation)

    assert evaluation.passed is False
    assert evaluation.missing_required == frozenset({CommunicationLabel.REQUEST})
    assert evaluation.unexpected == frozenset(
        {CommunicationLabel.PERSONAL_EVALUATION}
    )
    assert evaluation.forbidden_detected == frozenset(
        {CommunicationLabel.PERSONAL_EVALUATION}
    )


def test_label_evaluation_accepts_any_required_alternative() -> None:
    result = result_with_labels(CommunicationLabel.REQUEST)
    expectation = LabelExpectation(
        required=frozenset(),
        allowed=frozenset({CommunicationLabel.REQUEST, CommunicationLabel.DEMAND}),
        required_any=(
            frozenset({CommunicationLabel.REQUEST, CommunicationLabel.DEMAND}),
        ),
    )

    assert evaluate_labels(result, expectation).passed is True
