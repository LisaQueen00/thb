import json
from pathlib import Path

GOLDEN_SET_PATH = Path(__file__).with_name("pragmatic_meaning_v01.json")


def load_cases() -> list[dict[str, object]]:
    return json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))


def test_pragmatic_golden_set_covers_required_pairs_and_boundaries() -> None:
    cases = load_cases()
    ids = {str(case["id"]) for case in cases}

    assert len(cases) >= 10
    assert len(ids) == len(cases)
    assert {
        "improvement",
        "comparative_improvement",
        "repetition",
        "negative_question",
        "normative_responsibility",
        "neutral_request",
        "neutral_notice",
        "upward_report",
        "explicit_consequence",
        "ambiguous_combination",
        "new_communication_routine",
        "neutral_status_question",
    } <= ids


def test_pragmatic_golden_expectations_keep_uncertainty_boundaries() -> None:
    for case in load_cases():
        expected = str(case["expected_meaning"])
        assert expected.strip()
        assert all(term not in expected for term in case["forbidden"])
