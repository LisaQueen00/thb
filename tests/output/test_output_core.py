import pytest
from tests.output.helpers import make_output_request

from thb_input.output.composers import compose_output
from thb_input.output.errors import OutputError, OutputErrorCode
from thb_input.output.input_adapter import adapt_input
from thb_input.output.service import OutputService
from thb_input.output.validation import validate_output


def test_plain_language_and_reply_are_preserved_exactly() -> None:
    request = make_output_request()
    output = OutputService().process(request)
    assert output.plain_language.content == request.extract_result.event_summary
    assert output.reply.content == request.respond_result.reply
    assert output.reply.copyable is True


def test_counterparty_demand_is_not_upgraded_to_user_obligation() -> None:
    request = make_output_request(
        extract_updates={
            "requests": [
                {
                    "request_id": "req_001",
                    "actor": "other",
                    "target": "user",
                    "action": "今天完成文件",
                    "requested_time": "今天",
                    "strength": "demand",
                    "source": "other",
                    "supporting_segments": ["seg_001"],
                }
            ]
        }
    )
    output = OutputService().process(request)
    assert output.counterparty_request.actions == ["对方要求你今天完成文件"]
    assert "你需要" not in "".join(output.counterparty_request.actions)
    assert output.counterparty_request.requested_time == ["对方希望时间为今天"]


def test_user_reported_counterparty_request_keeps_its_source_boundary() -> None:
    output = OutputService().process(
        make_output_request(
            extract_updates={
                "requests": [
                    {
                        "request_id": "req_001",
                        "actor": "other",
                        "target": "user",
                        "action": "补交材料",
                        "requested_time": "明天",
                        "strength": "request",
                        "source": "user_context",
                        "supporting_segments": [],
                    }
                ]
            }
        )
    )
    assert output.counterparty_request.actions == [
        "根据你提供的背景，对方希望你补交材料"
    ]
    assert output.counterparty_request.requested_time == [
        "根据你提供的背景，对方希望时间为明天"
    ]


def test_request_time_takes_precedence_over_duplicate_time_constraint() -> None:
    output = OutputService().process(
        make_output_request(
            extract_updates={
                "requests": [
                    {
                        "request_id": "req_001",
                        "actor": "other",
                        "target": "user",
                        "action": "提交结果",
                        "requested_time": "今晚至明早",
                        "strength": "demand",
                        "source": "other",
                        "supporting_segments": ["seg_001"],
                    }
                ],
                "time_constraints": [
                    {
                        "time_id": "time_001",
                        "expression": "今晚完成、明早看到结果",
                        "type": "requested_deadline",
                        "epistemic_status": "reported_by_other",
                        "source": "other",
                        "supporting_segments": ["seg_001"],
                    }
                ],
            }
        )
    )
    assert output.counterparty_request.requested_time == ["对方希望时间为今晚至明早"]


def test_claim_sources_remain_visible() -> None:
    request = make_output_request(
        extract_updates={
            "claims": [
                {
                    "claim_id": "claim_001",
                    "content": "用户此前答应今天完成",
                    "source": "other",
                    "epistemic_status": "reported_by_other",
                    "supporting_segments": ["seg_001"],
                }
            ]
        }
    )
    output = OutputService().process(request)
    assert output.event_logic.prior_events == ["对方表示：用户此前答应今天完成"]


def test_unresolved_conflict_is_preserved() -> None:
    conflict = {
        "conflict_id": "conflict_001",
        "topic": "交付期限",
        "positions": [
            {"source": "other", "content": "今天", "supporting_segments": ["seg_001"]},
            {"source": "user_context", "content": "周一", "supporting_segments": []},
        ],
        "resolution": "unresolved",
    }
    output = OutputService().process(
        make_output_request(extract_updates={"conflicts": [conflict]})
    )
    assert len(output.event_logic.conflicts) == 1
    assert "双方说法不一致" in output.event_logic.conflicts[0]
    assert output.attention == output.event_logic.conflicts


def test_high_unknown_and_risk_are_selected_without_filling_unknown() -> None:
    request = make_output_request(
        extract_updates={
            "unknowns": [
                {
                    "unknown_id": "unknown_001",
                    "description": "责任范围是否已确认",
                    "importance": "high",
                    "reason": "影响责任判断",
                }
            ],
            "risks": [
                {
                    "risk_id": "risk_001",
                    "risk_type": "responsibility_risk",
                    "description": "存在扩大责任范围的风险",
                    "confidence": "high",
                    "basis": "对方提出全部责任由用户承担",
                    "supporting_segments": ["seg_001"],
                }
            ],
        }
    )
    output = OutputService().process(request)
    assert "目前无法确认：责任范围是否已确认" in output.event_logic.unknowns
    assert not any("责任属于" in item for item in output.attention)
    assert len(output.attention) == 2


def test_complex_event_logic_uses_readable_deterministic_templates() -> None:
    output = OutputService().process(
        make_output_request(
            extract_updates={
                "time_constraints": [
                    {
                        "time_id": "time_001",
                        "expression": "今天",
                        "type": "claimed_agreed_deadline",
                        "epistemic_status": "reported_by_other",
                        "source": "other",
                        "supporting_segments": ["seg_001"],
                    },
                    {
                        "time_id": "time_002",
                        "expression": "周一",
                        "type": "user_reported_deadline",
                        "epistemic_status": "reported_by_user",
                        "source": "user_context",
                        "supporting_segments": [],
                    },
                ],
                "responsibilities": [
                    {
                        "responsibility_id": "responsibility_001",
                        "actor": "user",
                        "content": "承担全部后续问题",
                        "source": "other",
                        "epistemic_status": "reported_by_other",
                        "basis": "对方的单方面表述",
                        "supporting_segments": ["seg_001"],
                    }
                ],
                "event_relationships": [
                    {
                        "relationship_id": "relationship_001",
                        "type": "claimed_causality",
                        "from_reference": "未在今天完成",
                        "to_reference": "后续问题",
                        "description": "对方将未在今天完成与后续问题相关联",
                        "epistemic_status": "reported_by_other",
                        "supporting_segments": ["seg_001"],
                    }
                ],
                "conditions_and_consequences": [
                    {
                        "relation_id": "condition_001",
                        "kind": "explicit_consequence",
                        "content": "对方称未完成会产生后续问题",
                        "source": "other",
                        "epistemic_status": "reported_by_other",
                        "confidence": "high",
                        "supporting_segments": ["seg_001"],
                    }
                ],
            }
        )
    )
    assert output.event_logic.time_logic == [
        "对方称此前约定时间是今天",
        "你提供的背景时间是周一",
    ]
    assert output.event_logic.responsibility_logic == [
        "对方表示：你的责任被描述为：承担全部后续问题"
    ]
    assert output.event_logic.dependencies == [
        "对方将未在今天完成与后续问题相关联"
    ]
    assert output.counterparty_request.claimed_consequences == [
        "对方称未完成会产生后续问题"
    ]


def test_healthy_communication_has_no_attention_section_content() -> None:
    assert OutputService().process(make_output_request()).attention == []


def test_strategy_display_contains_goal_actions_and_protected_boundary() -> None:
    output = OutputService().process(make_output_request())
    assert output.strategy.strategy_option_id == "strategy_001"
    assert output.strategy.key_actions
    assert "不要接受" in output.strategy.summary


def test_mismatched_respond_strategy_is_rejected() -> None:
    request = make_output_request(respond_updates={"strategy_option_id": "strategy_002"})
    with pytest.raises(OutputError) as caught:
        OutputService().process(request)
    assert caught.value.code is OutputErrorCode.INPUT_CONTRACT_MISMATCH


def test_mismatched_applied_constraints_are_rejected() -> None:
    request = make_output_request(
        respond_updates={
            "applied_constraints": {
                "tone": "warm",
                "boundary_level": "medium",
                "commitment_level": "limited",
            }
        }
    )
    with pytest.raises(OutputError) as caught:
        OutputService().process(request)
    assert caught.value.code is OutputErrorCode.INPUT_CONTRACT_MISMATCH


def test_validator_rejects_any_non_deterministic_content() -> None:
    request = make_output_request()
    model_input = adapt_input(request)
    output = compose_output(model_input)
    output.event_logic.current_state.append("不存在于 Extract 的新事实")
    with pytest.raises(OutputError) as caught:
        validate_output(output, model_input)
    assert caught.value.code is OutputErrorCode.OUTPUT_VALIDATION_FAILED
