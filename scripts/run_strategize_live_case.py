"""Run Strategize alone with a synthetic validated deadline-conflict Event Model."""

import json

from thb_input.api.v1.strategize import get_strategize_service
from thb_input.extract.schemas import ExtractResult
from thb_input.strategize.schemas import StrategizeRequest, UserGoalInput


def build_event_model() -> ExtractResult:
    return ExtractResult.model_validate(
        {
            "analysis_version": "0.1",
            "event_summary": (
                "对方主张用户承诺今天交付；用户称双方确认的是周一，期限冲突未解决。"
            ),
            "participants": [],
            "claims": [
                {
                    "claim_id": "claim_001",
                    "content": "对方主张用户承诺今天交付。",
                    "source": "other",
                    "epistemic_status": "reported_by_other",
                    "supporting_segments": ["seg_001"],
                },
                {
                    "claim_id": "claim_002",
                    "content": "用户称双方确认的是周一。",
                    "source": "user_context",
                    "epistemic_status": "reported_by_user",
                    "supporting_segments": [],
                },
            ],
            "requests": [],
            "commitments": [],
            "time_constraints": [],
            "responsibilities": [],
            "conditions_and_consequences": [],
            "event_relationships": [],
            "presuppositions": [],
            "implicit_meanings": [],
            "possible_intentions": [],
            "conflicts": [
                {
                    "conflict_id": "conflict_001",
                    "topic": "交付期限",
                    "positions": [
                        {
                            "source": "other",
                            "content": "对方称期限为今天。",
                            "supporting_segments": ["seg_001"],
                        },
                        {
                            "source": "user_context",
                            "content": "用户称期限为周一。",
                            "supporting_segments": [],
                        },
                    ],
                    "resolution": "unresolved",
                }
            ],
            "unknowns": [],
            "risks": [],
        }
    )


def main() -> None:
    result = get_strategize_service().process(
        StrategizeRequest(
            extract_result=build_event_model(),
            user_goal=UserGoalInput(content="保证推进，同时不承认未经确认的期限"),
            context=None,
        )
    )
    print(
        json.dumps(
            {
                "options": [
                    {
                        "id": option.option_id,
                        "type": option.strategy_type,
                        "must_include": option.reply_constraints.must_include,
                        "what_to_accept": option.what_to_accept,
                    }
                    for option in result.options
                ],
                "recommended": result.recommended_option_id,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
