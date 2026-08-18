import json

from thb_input.config import get_settings
from thb_input.respond.llm import OpenAICompatibleRespondLLMClient
from thb_input.respond.schemas import RespondRequest
from thb_input.respond.service import RespondService


def build_live_request() -> RespondRequest:
    return RespondRequest.model_validate(
        {
            "selected_strategy": {
                "option_id": "strategy_001",
                "strategy_type": "clarify",
                "title": "先确认交付期限",
                "goal": "在不承认争议期限的前提下确认实际安排",
                "key_actions": ["说明目前仍在处理", "请对方确认期望时间"],
                "what_to_accept": ["对方希望了解明确进度"],
                "what_not_to_accept": ["今天是双方已经确认的期限"],
                "clarification_needed": ["对方期望的具体时间"],
                "benefits": ["避免错误承诺并推动确认"],
                "tradeoffs": ["需要等待对方回复"],
                "risks": ["措辞过长可能引发新的争论"],
                "prerequisites": [],
                "reply_constraints": {
                    "must_include": ["目前还在处理中", "请对方确认期望时间"],
                    "must_not_include": ["承认今天是原定期限", "保证今天完成"],
                    "tone": "neutral",
                    "boundary_level": "medium",
                    "commitment_level": "limited",
                },
            },
            "relevant_event_context": {
                "event_summary": "对方要求用户今天交付，但期限是否共同确认存在争议。",
                "relevant_participants": ["用户", "对方"],
                "relevant_requests": ["对方要求今天交付"],
                "relevant_time_constraints": ["对方主张今天，双方是否确认未知"],
            },
        }
    )


def main() -> None:
    settings = get_settings()
    service = RespondService(
        OpenAICompatibleRespondLLMClient(settings),
        validation_retries=settings.respond_validation_retries,
    )
    output = service.process(build_live_request()).model_dump(mode="json")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
