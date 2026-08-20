import json
from pathlib import Path

GOLDEN_SET_PATH = Path(__file__).with_name("minimal_product_v01.json")


def test_meaning_only_golden_set_is_complete() -> None:
    cases = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))

    assert len(cases) >= 18
    assert len({case["id"] for case in cases}) == len(cases)
    required = {"id", "source_message", "context", "expected_meaning"}
    assert all(set(case) == required for case in cases)
    assert all(case["source_message"].strip() for case in cases)
    assert all(case["expected_meaning"].strip() for case in cases)


def test_golden_meanings_are_observational_not_action_prescriptions() -> None:
    cases = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    prohibited = ("应该回复", "建议回复", "可以回复", "回复对方")
    assert all(
        not any(term in case["expected_meaning"] for term in prohibited)
        for case in cases
    )


def test_implicit_premise_and_false_positive_cases_are_present() -> None:
    cases = {
        case["id"]: case
        for case in json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    }
    required = {
        "implicit_work_priority",
        "implicit_timely_communication",
        "implicit_advance_notice",
        "implicit_repeated_delay",
        "new_daily_report_requirement",
        "implicit_claimed_responsibility",
        "implicit_unconfirmed_status_question",
        "neutral_meeting_notice",
        "neutral_material_request",
        "neutral_template_change",
        "neutral_upward_report",
        "report_with_unknown_content",
    }
    assert required <= cases.keys()

    neutral_ids = {
        "new_daily_report_requirement",
        "neutral_meeting_notice",
        "neutral_material_request",
        "neutral_template_change",
        "neutral_upward_report",
    }
    false_positive_markers = ("做得不好", "不满", "责任争议", "施压", "威胁", "隐藏目的")
    for case_id in neutral_ids:
        assert not any(
            marker in cases[case_id]["expected_meaning"]
            for marker in false_positive_markers
        )
