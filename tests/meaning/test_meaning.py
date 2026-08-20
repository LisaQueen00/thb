from tests.extract.helpers import empty_result

from thb_input.extract.schemas import ExtractResult
from thb_input.meaning import MeaningService


def make_extract(
    candidates: list[dict[str, object]],
    *,
    event_summary: str = "这是不应被公开复用的 Extract 摘要。",
) -> ExtractResult:
    payload = empty_result(event_summary)
    payload["meaning_selection"] = {"candidates": candidates}
    return ExtractResult.model_validate(payload)


def candidate(
    content: str,
    kind: str = "core_speech_act",
    *,
    confidence: str = "high",
    materiality: str = "high",
) -> dict[str, object]:
    return {
        "content": content,
        "kind": kind,
        "confidence": confidence,
        "materiality": materiality,
        "basis": "Structured Extract evidence.",
        "supporting_segments": ["seg_001"],
    }


def test_meaning_is_not_event_summary_alias() -> None:
    extracted = make_extract([candidate("讲话者请求用户确认文件")])
    result = MeaningService().process(extracted)
    assert result.meaning == "对方请求你确认文件。"
    assert result.meaning != extracted.event_summary


def test_material_stance_precedes_core_and_routine_unknown_is_excluded() -> None:
    extracted = make_extract(
        [
            candidate("讲话者要求用户调整好工作优先级"),
            candidate(
                "讲话者认为用户目前的工作优先级安排未达到其预期",
                "material_stance",
            ),
            candidate(
                "具体排序标准和完成时间未说明",
                "fact_boundary",
                materiality="low",
            ),
        ]
    )
    result = MeaningService().process(extracted)
    assert result.meaning == (
        "对方认为你目前的工作优先级安排未达到其预期；"
        "对方要求你调整好工作优先级。"
    )
    assert "排序标准" not in result.meaning
    assert "完成时间" not in result.meaning


def test_material_fact_boundary_is_preserved() -> None:
    extracted = make_extract(
        [
            candidate("讲话者在确认事项是否完成"),
            candidate("讲话者倾向认为事项可能尚未完成", "material_stance"),
            candidate("实际完成状态仍未确认", "fact_boundary"),
        ]
    )
    result = MeaningService().process(extracted)
    assert "倾向认为事项可能尚未完成" in result.meaning
    assert "实际完成状态仍未确认" in result.meaning


def test_low_confidence_motive_is_excluded() -> None:
    extracted = make_extract(
        [
            candidate("讲话者表示已经向负责人汇报"),
            candidate(
                "讲话者提及负责人是为了施压",
                "material_stance",
                confidence="low",
            ),
        ]
    )
    result = MeaningService().process(extracted)
    assert result.meaning == "对方表示已经向负责人汇报。"
    assert "施压" not in result.meaning


def test_near_duplicate_candidates_are_collapsed() -> None:
    extracted = make_extract(
        [
            candidate("讲话者要求用户今天确认文件"),
            candidate("讲话者要求用户今天确认文件。"),
        ]
    )
    result = MeaningService().process(extracted)
    assert result.meaning == "对方要求你今天确认文件。"
