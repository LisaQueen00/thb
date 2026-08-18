from tests.output.helpers import make_output_request

from thb_input.output.schemas import EventLogic
from thb_input.output.service import OutputService


def request(
    index: int,
    action: str,
    *,
    requested_time: str | None = None,
    strength: str = "request",
) -> dict[str, object]:
    return {
        "request_id": f"req_{index:03d}",
        "actor": "other",
        "target": "user",
        "action": action,
        "requested_time": requested_time,
        "strength": strength,
        "source": "other",
        "supporting_segments": ["seg_001"],
    }


def claim(index: int, content: str, source: str = "other") -> dict[str, object]:
    return {
        "claim_id": f"claim_{index:03d}",
        "content": content,
        "source": source,
        "epistemic_status": (
            "reported_by_other" if source == "other" else "reported_by_user"
        ),
        "supporting_segments": ["seg_001"] if source == "other" else [],
    }


def time_constraint(
    index: int,
    expression: str,
    kind: str,
    source: str,
) -> dict[str, object]:
    return {
        "time_id": f"time_{index:03d}",
        "expression": expression,
        "type": kind,
        "epistemic_status": (
            "reported_by_other" if source == "other" else "reported_by_user"
        ),
        "source": source,
        "supporting_segments": ["seg_001"] if source == "other" else [],
    }


def unresolved_deadline() -> dict[str, object]:
    return {
        "conflict_id": "conflict_001",
        "topic": "交付期限",
        "positions": [
            {"source": "other", "content": "今天", "supporting_segments": ["seg_001"]},
            {"source": "user_context", "content": "周一", "supporting_segments": []},
        ],
        "resolution": "unresolved",
    }


def test_01_ordinary_direct_communication() -> None:
    output = OutputService().process(
        make_output_request(
            extract_updates={"requests": [request(1, "确认文件")]}
        )
    )
    assert output.counterparty_request.actions == ["对方希望你确认文件"]
    assert output.attention == []


def test_02_aggressive_expression_does_not_hide_real_request() -> None:
    output = OutputService().process(
        make_output_request(
            extract_updates={
                "event_summary": "对方使用攻击性评价，同时要求用户发送项目进度。",
                "requests": [request(1, "发送项目进度", strength="demand")],
                "risks": [
                    {
                        "risk_id": "risk_001",
                        "risk_type": "escalation_risk",
                        "description": "回应人身攻击可能扩大冲突",
                        "confidence": "high",
                        "basis": "沟通中存在攻击性评价",
                        "supporting_segments": ["seg_001"],
                    }
                ],
            }
        )
    )
    assert output.counterparty_request.actions == ["对方要求你发送项目进度"]
    assert all("人格" not in item for item in output.counterparty_request.actions)
    assert len(output.attention) == 1


def test_03_deadline_conflict_remains_unresolved() -> None:
    output = OutputService().process(
        make_output_request(
            extract_updates={
                "event_summary": "对方要求今天完成，用户背景称时间是周一，期限存在冲突。",
                "requests": [request(1, "完成文件", requested_time="今天", strength="demand")],
                "time_constraints": [
                    time_constraint(1, "今天", "requested_deadline", "other"),
                    time_constraint(2, "周一", "user_reported_deadline", "user_context"),
                ],
                "conflicts": [unresolved_deadline()],
            }
        )
    )
    rendered = output.model_dump_json()
    assert "双方说法不一致" in output.event_logic.conflicts[0]
    assert "对方要求你完成文件" in output.counterparty_request.actions[0]
    assert "你本来就应该今天完成" not in rendered
    assert output.event_logic.conflicts[0] in output.attention


def test_04_responsibility_pressure_remains_a_counterparty_claim() -> None:
    output = OutputService().process(
        make_output_request(
            extract_updates={
                "responsibilities": [
                    {
                        "responsibility_id": "responsibility_001",
                        "actor": "user",
                        "content": "全部损失由用户承担",
                        "source": "other",
                        "epistemic_status": "reported_by_other",
                        "basis": "对方称损失都算用户的",
                        "supporting_segments": ["seg_001"],
                    }
                ],
                "conditions_and_consequences": [
                    {
                        "relation_id": "condition_001",
                        "kind": "explicit_consequence",
                        "content": "对方称全部损失都算用户的",
                        "source": "other",
                        "epistemic_status": "reported_by_other",
                        "confidence": "high",
                        "supporting_segments": ["seg_001"],
                    }
                ],
            }
        )
    )
    assert output.counterparty_request.claimed_consequences == [
        "对方称全部损失都算用户的"
    ]
    assert output.event_logic.responsibility_logic == [
        "对方表示：你的责任被描述为：全部损失由用户承担"
    ]
    assert "用户已经承担" not in output.model_dump_json()


def test_05_medium_implicit_consequence_stays_possible() -> None:
    output = OutputService().process(
        make_output_request(
            extract_updates={
                "implicit_meanings": [
                    {
                        "implicit_id": "imp_001",
                        "content": "未按要求处理可能带来未说明的负面后果",
                        "confidence": "medium",
                        "basis": "对方说之后别说没提醒",
                        "supporting_segments": ["seg_001"],
                    }
                ]
            }
        )
    )
    assert output.attention == [
        "这段表达可能意味着：未按要求处理可能带来未说明的负面后果"
    ]
    assert "确定意图" not in output.model_dump_json()


def test_06_friendly_communication_does_not_manufacture_risk() -> None:
    output = OutputService().process(
        make_output_request(
            extract_updates={
                "event_summary": "对方友好询问用户是否方便查看资料。",
                "requests": [request(1, "查看资料")],
            }
        )
    )
    assert output.attention == []
    rendered = output.model_dump_json()
    assert all(word not in rendered for word in ("操控", "隐藏意图", "施压"))


def test_07_complex_event_stays_compact_and_does_not_dump_extract() -> None:
    claims = [claim(index, f"当前事项状态{index}") for index in range(1, 6)]
    requests = [request(index, f"处理事项{index}") for index in range(1, 6)]
    times = [
        time_constraint(index, f"时间{index}", "requested_deadline", "other")
        for index in range(1, 6)
    ]
    unknowns = [
        {
            "unknown_id": f"unknown_{index:03d}",
            "description": f"未知事项{index}",
            "importance": "high",
            "reason": "影响处理选择",
        }
        for index in range(1, 6)
    ]
    output = OutputService().process(
        make_output_request(
            extract_updates={
                "claims": claims,
                "requests": requests,
                "time_constraints": times,
                "conflicts": [unresolved_deadline()],
                "unknowns": unknowns,
            }
        )
    )
    assert _logic_item_count(output.event_logic) <= 14
    assert len(output.counterparty_request.actions) <= 3
    assert len(output.attention) <= 3
    rendered = output.model_dump_json()
    assert all(token not in rendered for token in ("claim_", "req_", "seg_", "epistemic_status"))
    assert output.event_logic.conflicts
    assert output.event_logic.unknowns


def _logic_item_count(logic: EventLogic) -> int:
    payload = logic.model_dump()
    return sum(len(items) for items in payload.values())
