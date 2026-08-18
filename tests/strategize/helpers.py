from tests.extract.helpers import empty_result

from thb_input.extract.schemas import ExtractResult
from thb_input.strategize.schemas import StrategizeRequest, UserGoalInput


def make_request(
    *,
    user_goal: str | None = None,
    extract_updates: dict[str, object] | None = None,
    context: str | None = None,
) -> StrategizeRequest:
    payload = empty_result("当前存在一项需要处理的沟通事务。")
    payload.update(extract_updates or {})
    return StrategizeRequest(
        extract_result=ExtractResult.model_validate(payload),
        user_goal=UserGoalInput(content=user_goal) if user_goal else None,
        context=context,
    )


def option(
    option_id: str,
    strategy_type: str,
    *,
    actions: list[str] | None = None,
    commitment_level: str = "limited",
) -> dict[str, object]:
    return {
        "option_id": option_id,
        "strategy_type": strategy_type,
        "title": f"{strategy_type}方案",
        "goal": "在保留事实边界的前提下处理当前事项。",
        "key_actions": actions or ["确认当前实际进度并说明下一步"],
        "what_to_accept": ["确认当前能够核实的事项状态"],
        "what_not_to_accept": ["不承认未经确认的责任或承诺"],
        "clarification_needed": [],
        "benefits": ["保持事项可推进"],
        "tradeoffs": ["需要增加一次沟通"],
        "risks": [],
        "prerequisites": [],
        "reply_constraints": {
            "must_include": ["当前可确认的事实"],
            "must_not_include": ["未经确认的承诺"],
            "tone": "neutral",
            "boundary_level": "medium",
            "commitment_level": commitment_level,
        },
    }


def strategy_result(
    *,
    explicit_goal: str | None = None,
    options: list[dict[str, object]] | None = None,
    recommended: str | None = "strategy_001",
) -> dict[str, object]:
    return {
        "strategy_version": "0.1",
        "user_goal": {
            "source": "explicit_user_input" if explicit_goal else "default_options",
            "content": explicit_goal,
        },
        "strategy_context": {
            "key_conflicts": [],
            "key_unknowns": [],
            "key_risks": [],
        },
        "required_user_input": [],
        "options": options
        or [
            option("strategy_001", "progress"),
            option("strategy_002", "clarify"),
        ],
        "recommended_option_id": recommended,
        "custom_strategy_supported": True,
    }


class FakeLLM:
    def __init__(self, *responses: object) -> None:
        self.responses = list(responses)
        self.prompts: list[object] = []

    def complete_structured(self, prompt: object) -> object:
        self.prompts.append(prompt)
        return self.responses.pop(0)
