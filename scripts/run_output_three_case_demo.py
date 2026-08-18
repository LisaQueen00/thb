import json

from thb_input.extract.schemas import ExtractResult
from thb_input.output.schemas import OutputRequest
from thb_input.output.service import OutputService
from thb_input.respond.schemas import RespondResult
from thb_input.strategize.schemas import StrategyOption


def make_output_request(
    *,
    extract_updates: dict[str, object],
    strategy_updates: dict[str, object],
    respond_updates: dict[str, object],
) -> OutputRequest:
    extract: dict[str, object] = {
        "analysis_version": "0.1",
        "event_summary": "当前存在一项沟通事务。",
        "participants": [],
        "claims": [],
        "requests": [],
        "commitments": [],
        "time_constraints": [],
        "responsibilities": [],
        "conditions_and_consequences": [],
        "event_relationships": [],
        "presuppositions": [],
        "implicit_meanings": [],
        "possible_intentions": [],
        "conflicts": [],
        "unknowns": [],
        "risks": [],
    }
    extract.update(extract_updates)
    strategy: dict[str, object] = {
        "option_id": "strategy_001",
        "strategy_type": "progress",
        "title": "推进当前事项",
        "goal": "推进当前事项",
        "key_actions": ["确认下一步"],
        "what_to_accept": [],
        "what_not_to_accept": [],
        "clarification_needed": [],
        "benefits": ["推进当前事项"],
        "tradeoffs": ["需要进行一次回复"],
        "risks": [],
        "prerequisites": [],
        "reply_constraints": {},
    }
    strategy.update(strategy_updates)
    response: dict[str, object] = {
        "respond_version": "0.1",
        "strategy_option_id": "strategy_001",
        **respond_updates,
    }
    return OutputRequest(
        extract_result=ExtractResult.model_validate(extract),
        selected_strategy=StrategyOption.model_validate(strategy),
        respond_result=RespondResult.model_validate(response),
    )


def constraints(
    must_include: list[str],
    must_not_include: list[str],
    tone: str,
    boundary: str,
) -> dict[str, object]:
    return {
        "must_include": must_include,
        "must_not_include": must_not_include,
        "tone": tone,
        "boundary_level": boundary,
        "commitment_level": "limited",
    }


def main() -> None:
    cases = [
        (
            "语气友好",
            "方便的话，能不能今天帮我确认一下文件？不着急，有结果告诉我就好，谢谢。",
            make_output_request(
                extract_updates={
                    "event_summary": "对方礼貌询问用户能否今天确认文件，并希望确认后获知结果。",
                    "requests": [
                        {
                            "request_id": "req_001",
                            "actor": "other",
                            "target": "user",
                            "action": "确认文件并告知结果",
                            "requested_time": "今天",
                            "strength": "request",
                            "source": "other",
                            "supporting_segments": ["seg_001"],
                        }
                    ],
                    "time_constraints": [
                        {
                            "time_id": "time_001",
                            "expression": "今天",
                            "type": "requested_deadline",
                            "epistemic_status": "reported_by_other",
                            "source": "other",
                            "supporting_segments": ["seg_001"],
                        }
                    ],
                },
                strategy_updates={
                    "title": "自然回应并推进文件确认",
                    "goal": "今天确认文件情况并告知对方",
                    "key_actions": ["今天确认文件情况"],
                    "what_not_to_accept": [],
                    "reply_constraints": constraints(
                        ["今天确认文件情况"], [], "warm", "low"
                    ),
                },
                respond_updates={
                    "reply": "可以，我今天确认文件情况。",
                    "applied_constraints": {
                        "tone": "warm",
                        "boundary_level": "low",
                        "commitment_level": "limited",
                    },
                },
            ),
        ),
        (
            "无边界感",
            "你今晚必须把这个做完，别跟我说有什么困难，反正我明早必须看到结果。",
            make_output_request(
                extract_updates={
                    "event_summary": (
                        "对方单方面要求用户今晚完成并在明早提供结果；"
                        "用户能否按时完成尚未确认。"
                    ),
                    "requests": [
                        {
                            "request_id": "req_001",
                            "actor": "other",
                            "target": "user",
                            "action": "今晚完成并在明早提供结果",
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
                    "unknowns": [
                        {
                            "unknown_id": "unknown_001",
                            "description": "用户今晚是否能够完成",
                            "importance": "high",
                            "reason": "决定是否能够作出时间承诺",
                        }
                    ],
                },
                strategy_updates={
                    "strategy_type": "boundary",
                    "title": "说明能力边界并给出确认安排",
                    "goal": "不接受单方面设定的期限，同时提供下一步安排",
                    "key_actions": ["说明今晚无法确认完成", "明早确认后回复"],
                    "what_not_to_accept": ["今晚是双方已经约定的期限"],
                    "reply_constraints": constraints(
                        ["今晚无法确认完成", "明早确认后回复"],
                        ["承认今晚是已约定期限", "保证今晚完成"],
                        "firm",
                        "medium",
                    ),
                },
                respond_updates={
                    "reply": "今晚无法确认完成，明早确认后回复。",
                    "applied_constraints": {
                        "tone": "firm",
                        "boundary_level": "medium",
                        "commitment_level": "limited",
                    },
                },
            ),
        ),
        (
            "肆意发泄",
            "你到底会不会做事？每次都拖拖拉拉，真是让人恶心。你这种人根本不靠谱，赶紧把项目进度发给我！",
            make_output_request(
                extract_updates={
                    "event_summary": "对方在使用多个人身评价的同时，要求用户提供项目进度。",
                    "requests": [
                        {
                            "request_id": "req_001",
                            "actor": "other",
                            "target": "user",
                            "action": "提供项目进度",
                            "requested_time": None,
                            "strength": "demand",
                            "source": "other",
                            "supporting_segments": ["seg_001"],
                        }
                    ],
                    "risks": [
                        {
                            "risk_id": "risk_001",
                            "risk_type": "escalation_risk",
                            "description": "持续回应人身评价可能扩大无意义冲突",
                            "confidence": "high",
                            "basis": "原沟通包含多个人身评价",
                            "supporting_segments": ["seg_001"],
                        }
                    ],
                },
                strategy_updates={
                    "strategy_type": "boundary",
                    "title": "回应事务要求并明确沟通边界",
                    "goal": "继续处理项目事项，同时拒绝人身评价",
                    "key_actions": ["继续同步项目进度", "明确不接受针对个人的评价"],
                    "what_not_to_accept": ["对用户人格的负面评价"],
                    "reply_constraints": constraints(
                        ["项目进度会继续同步", "不接受针对个人的评价"],
                        ["回击对方", "评价对方人格", "承担延误责任"],
                        "firm",
                        "high",
                    ),
                },
                respond_updates={
                    "reply": "项目进度会继续同步，但不接受针对个人的评价。请就项目本身进行沟通。",
                    "applied_constraints": {
                        "tone": "firm",
                        "boundary_level": "high",
                        "commitment_level": "limited",
                    },
                },
            ),
        ),
    ]
    service = OutputService()
    output = [
        {
            "case": name,
            "original_text": original,
            "output": service.process(request).model_dump(mode="json"),
        }
        for name, original, request in cases
    ]
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
