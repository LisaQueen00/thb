import pytest
from tests.meaning.test_meaning import candidate, make_extract

from thb_input.meaning import MeaningService

CASES = [
    (
        "ordinary_request",
        [candidate("讲话者希望今天下午收到最新版")],
        ["今天下午收到最新版"],
        ["文件格式", "具体几点"],
    ),
    ("ordinary_notice", [candidate("讲话者通知明天下午三点开会")], ["明天下午三点开会"], ["不满"]),
    (
        "current_correction",
        [
            candidate("讲话者要求用户调整好优先级"),
            candidate("讲话者认为用户目前的优先级安排未达到其预期", "material_stance"),
        ],
        ["未达到其预期", "调整好优先级"],
        ["排序标准", "完成时间"],
    ),
    (
        "future_requirement",
        [candidate("讲话者要求用户明天合理安排工作优先级")],
        ["明天合理安排"],
        ["当前安排未达到"],
    ),
    (
        "negative_question",
        [
            candidate("讲话者在确认事项是否完成"),
            candidate("讲话者倾向认为事项可能尚未完成", "material_stance"),
            candidate("实际状态仍未确认", "fact_boundary"),
        ],
        ["倾向认为", "仍未确认"],
        ["确实尚未完成"],
    ),
    (
        "neutral_confirmation",
        [candidate("讲话者在确认事项是否完成")],
        ["确认事项是否完成"],
        ["倾向认为尚未完成"],
    ),
    (
        "historical_repetition",
        [
            candidate("讲话者要求用户以后避免拖到最后处理"),
            candidate("讲话者认为此前发生过拖到最后才处理的情况", "material_stance"),
        ],
        ["此前发生过", "以后避免"],
        ["故意拖延"],
    ),
    (
        "responsibility",
        [
            candidate("讲话者要求用户在非工作时间保持响应"),
            candidate("讲话者把持续响应描述成用户本来就应承担的责任", "responsibility"),
        ],
        ["非工作时间保持响应", "本来就应承担的责任"],
        ["用户确实有义务"],
    ),
    (
        "commitment_boundary",
        [
            candidate("讲话者要求用户今晚交付初稿"),
            candidate("今晚交付并不是此前已经明确的承诺", "commitment"),
        ],
        ["今晚交付初稿", "不是此前已经明确的承诺"],
        [],
    ),
    (
        "consequence",
        [
            candidate("讲话者要求今天处理该事项"),
            candidate("讲话者以未说明的后续不利结果加强要求", "consequence"),
        ],
        ["今天处理", "后续不利结果"],
        ["具体后果是"],
    ),
    (
        "upward_report",
        [
            candidate("讲话者表示昨晚已经向负责人汇报"),
            candidate("具体汇报内容未说明", "fact_boundary"),
        ],
        ["已经向负责人汇报", "汇报内容未说明"],
        ["为了施压", "投诉"],
    ),
    (
        "emotion_and_transaction",
        [candidate("讲话者要求用户今天提交结果")],
        ["今天提交结果"],
        ["人格", "能力不足"],
    ),
]


@pytest.mark.parametrize(("case_id", "candidates", "required", "forbidden"), CASES)
def test_meaning_selection_cases(
    case_id: str,
    candidates: list[dict[str, object]],
    required: list[str],
    forbidden: list[str],
) -> None:
    meaning = MeaningService().process(make_extract(candidates)).meaning
    assert all(fragment in meaning for fragment in required), case_id
    assert not any(fragment in meaning for fragment in forbidden), case_id
