from thb_input.respond.schemas import RespondRequest


class FakeLLM:
    def __init__(self, *responses: object) -> None:
        self.responses = list(responses)
        self.prompts = []

    def complete_structured(self, prompt: object) -> object:
        self.prompts.append(prompt)
        return self.responses.pop(0)


def make_request(
    *,
    strategy_type: str = "progress",
    must_include: list[str] | None = None,
    must_not_include: list[str] | None = None,
    what_not_to_accept: list[str] | None = None,
    commitment_level: str = "limited",
    tone: str = "neutral",
    boundary_level: str = "medium",
    event_summary: str = "对方询问任务进度",
) -> RespondRequest:
    return RespondRequest.model_validate(
        {
            "selected_strategy": {
                "option_id": "strategy_001",
                "strategy_type": strategy_type,
                "title": "确认安排并推进",
                "goal": "确认交付安排",
                "key_actions": ["说明当前状态", "确认下一步"],
                "what_to_accept": ["对方需要了解进度"],
                "what_not_to_accept": what_not_to_accept or [],
                "clarification_needed": [],
                "benefits": ["推进事情"],
                "tradeoffs": ["需要等待确认"],
                "risks": [],
                "prerequisites": [],
                "reply_constraints": {
                    "must_include": must_include or ["目前还在处理中"],
                    "must_not_include": must_not_include or [],
                    "tone": tone,
                    "boundary_level": boundary_level,
                    "commitment_level": commitment_level,
                },
            },
            "relevant_event_context": {
                "event_summary": event_summary,
                "relevant_participants": ["对方", "用户"],
                "relevant_requests": ["说明当前状态"],
                "relevant_time_constraints": [],
            },
        }
    )


def result(
    reply: str = "目前还在处理中，有进展我会同步。",
    *,
    tone: str = "neutral",
    boundary_level: str = "medium",
    commitment_level: str = "limited",
) -> dict[str, object]:
    return {
        "respond_version": "0.1",
        "strategy_option_id": "strategy_001",
        "reply": reply,
        "applied_constraints": {
            "tone": tone,
            "boundary_level": boundary_level,
            "commitment_level": commitment_level,
        },
    }
