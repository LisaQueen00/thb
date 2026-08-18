"""Run one real Input -> Strip -> Extract -> Strategize acceptance case."""

import json

from thb_input.api.v1.extract import get_extract_service
from thb_input.api.v1.strategize import get_strategize_service
from thb_input.api.v1.strip import get_strip_service
from thb_input.extract.schemas import ExtractRequest
from thb_input.schemas.input import TextInputRequest
from thb_input.services.text_input import build_text_input_record
from thb_input.strategize.schemas import StrategizeRequest, UserGoalInput


def main() -> None:
    canonical = build_text_input_record(
        TextInputRequest(
            source_message="你明明答应今天交。",
            context="我们当时确认的是周一。",
        )
    )
    strip_result = get_strip_service().process(canonical)
    extract_result = get_extract_service().process(
        ExtractRequest(canonical_input=canonical, strip_result=strip_result)
    )
    strategy_result = get_strategize_service().process(
        StrategizeRequest(
            extract_result=extract_result,
            user_goal=UserGoalInput(content="保证事情推进，同时避免承认未经确认的期限"),
            context=canonical.context,
        )
    )
    print(
        json.dumps(
            {
                "strategy_version": strategy_result.strategy_version,
                "user_goal": strategy_result.user_goal.model_dump(mode="json"),
                "key_conflicts": strategy_result.strategy_context.key_conflicts,
                "required_user_input": [
                    item.model_dump(mode="json")
                    for item in strategy_result.required_user_input
                ],
                "options": [
                    {
                        "option_id": item.option_id,
                        "strategy_type": item.strategy_type,
                        "title": item.title,
                        "key_actions": item.key_actions,
                        "what_not_to_accept": item.what_not_to_accept,
                        "reply_constraints": item.reply_constraints.model_dump(
                            mode="json"
                        ),
                    }
                    for item in strategy_result.options
                ],
                "recommended_option_id": strategy_result.recommended_option_id,
                "custom_strategy_supported": (
                    strategy_result.custom_strategy_supported
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
