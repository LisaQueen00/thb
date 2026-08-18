import pytest

from thb_input.schemas.input import TextInputRequest
from thb_input.services.text_input import build_text_input_record
from thb_input.strip.acceptance import GOLDEN_CASES, LONG_CASES, GoldenCase
from thb_input.strip.evaluation import evaluate_labels
from thb_input.strip.service import StripService


class AcceptanceFakeLLMClient:
    def __init__(self, case: GoldenCase) -> None:
        self.case = case

    def complete_structured(self, prompt: object) -> object:
        labels = set(self.case.expectation.required)
        labels.update(
            min(group, key=lambda label: label.value)
            for group in self.case.expectation.required_any
        )
        return {
            "segments": [
                {
                    "text": self.case.source_message,
                    "labels": [label.value for label in labels],
                }
            ]
        }


def test_acceptance_dataset_has_unique_names_and_valid_expectations() -> None:
    cases = GOLDEN_CASES + LONG_CASES
    names = [case.name for case in cases]

    assert len(GOLDEN_CASES) == 12
    assert len(LONG_CASES) == 5
    assert len(names) == len(set(names))
    assert all(case.expectation.required <= case.expectation.allowed for case in cases)
    assert all(not (case.expectation.allowed & case.expectation.forbidden) for case in cases)
    assert all(
        all(group <= case.expectation.allowed for group in case.expectation.required_any)
        for case in cases
    )


@pytest.mark.parametrize("case", LONG_CASES, ids=lambda case: case.name)
def test_long_case_contract_and_golden_evaluation(case: GoldenCase) -> None:
    canonical_input = build_text_input_record(
        TextInputRequest(source_message=case.source_message, context=case.context)
    )
    result = StripService(AcceptanceFakeLLMClient(case)).process(canonical_input)

    assert result.segments[0].text == case.source_message
    assert evaluate_labels(result, case.expectation).passed is True
