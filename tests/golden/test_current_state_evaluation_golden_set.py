import json
from pathlib import Path

GOLDEN_SET_PATH = Path(__file__).with_name("current_state_evaluation_v01.json")


def load_cases() -> list[dict[str, object]]:
    return json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))


def test_current_state_cases_are_balanced_positive_and_boundary_pairs() -> None:
    cases = load_cases()
    positive = [case for case in cases if case["expected_stance"] is not None]
    boundary = [case for case in cases if case["expected_stance"] is None]

    assert len(cases) == 10
    assert len(positive) == len(boundary) == 5
    assert len({case["id"] for case in cases}) == len(cases)


def test_boundary_cases_define_forbidden_current_state_inferences() -> None:
    for case in load_cases():
        if case["expected_stance"] is None:
            assert case["forbidden_stances"]


def test_positive_cases_preserve_speaker_attribution() -> None:
    for case in load_cases():
        stance = case["expected_stance"]
        if stance is not None:
            assert str(stance).startswith("讲话者")
