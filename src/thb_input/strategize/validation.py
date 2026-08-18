from pydantic import ValidationError

from thb_input.extract.schemas import Confidence, RiskType
from thb_input.strategize.errors import StrategizeError, StrategizeErrorCode
from thb_input.strategize.schemas import (
    CommitmentLevel,
    StrategizeRequest,
    StrategizeResult,
    StrategyType,
    UserGoalSource,
)


def validate_schema(payload: object) -> StrategizeResult:
    try:
        return StrategizeResult.model_validate(payload)
    except ValidationError as exc:
        raise StrategizeError(
            StrategizeErrorCode.SCHEMA_VALIDATION_FAILED,
            f"Strategize result does not match the schema: {exc}",
        ) from exc


def validate_semantics(
    result: StrategizeResult, request: StrategizeRequest
) -> StrategizeResult:
    _validate_goal(result, request)
    _validate_options(result)
    _validate_event_boundaries(result, request)
    _validate_prohibited_output(result)
    return result


def _validate_goal(result: StrategizeResult, request: StrategizeRequest) -> None:
    if request.user_goal:
        if result.user_goal.source is not UserGoalSource.EXPLICIT:
            raise _semantic_error("explicit user goal must retain explicit_user_input source")
        if result.user_goal.content != request.user_goal.content:
            raise _semantic_error("explicit user goal must be preserved exactly")
    elif (
        result.user_goal.source is not UserGoalSource.DEFAULT
        or result.user_goal.content is not None
    ):
        raise _semantic_error("missing user goal must resolve to default_options and null")


def _validate_options(result: StrategizeResult) -> None:
    ids = [option.option_id for option in result.options]
    expected = [f"strategy_{index:03d}" for index in range(1, len(ids) + 1)]
    if ids != expected:
        raise _semantic_error("option IDs must be unique and sequential from strategy_001")
    types = [option.strategy_type for option in result.options]
    if len(types) != len(set(types)):
        raise _semantic_error("strategy options must use materially different strategy types")
    if result.recommended_option_id is not None and result.recommended_option_id not in ids:
        raise _semantic_error("recommended_option_id must reference an emitted option")

    vague_actions = {"保持冷静", "积极处理", "成熟沟通", "好好沟通", "冷静", "沟通"}
    for option in result.options:
        if any(action.strip() in vague_actions for action in option.key_actions):
            raise _semantic_error("key_actions contains non-actionable generic advice")
        if len(option.key_actions) != len(set(option.key_actions)):
            raise _semantic_error("key_actions contains duplicates")


def _validate_event_boundaries(
    result: StrategizeResult, request: StrategizeRequest
) -> None:
    event = request.extract_result
    unresolved = [item for item in event.conflicts if item.resolution == "unresolved"]
    if unresolved:
        if not result.strategy_context.key_conflicts:
            raise _semantic_error("unresolved Event Model conflicts must remain in context")
        if not any(
            option.strategy_type is StrategyType.CLARIFY for option in result.options
        ):
            raise _semantic_error("unresolved conflict requires a clarify option")
        if any(not option.what_not_to_accept for option in result.options):
            raise _semantic_error("conflict options must protect unsupported admissions")
        certainty_phrases = (
            "是双方确认",
            "已被双方确认",
            "双方已确认",
            "真实期限是",
            "实际期限是",
            "既定期限是",
        )
        for option in result.options:
            affirmative_fields = (
                [option.goal]
                + option.key_actions
                + option.what_to_accept
                + option.reply_constraints.must_include
            )
            if any(
                phrase in text
                for text in affirmative_fields
                for phrase in certainty_phrases
            ):
                raise _semantic_error(
                    "strategy upgrades an unresolved position to confirmed fact"
                )

    high_risks = [risk for risk in event.risks if risk.confidence is Confidence.HIGH]
    if high_risks and not result.strategy_context.key_risks:
        raise _semantic_error("high Event Model risks must remain in strategy_context")

    completion_unknown = any(
        any(marker in unknown.description for marker in ("完成时间", "预计时间", "可完成"))
        for unknown in event.unknowns
    )
    if completion_unknown and not result.required_user_input:
        raise _semantic_error("unknown completion time requires required_user_input")

    irreversible = any(
        risk.confidence is Confidence.HIGH
        and risk.risk_type
        in {RiskType.IRREVERSIBLE_ACTION, RiskType.COMMITMENT, RiskType.RESPONSIBILITY}
        for risk in event.risks
    )
    if irreversible:
        safe_types = {
            StrategyType.CLARIFY,
            StrategyType.RISK_REDUCTION,
            StrategyType.DELAY_AND_VERIFY,
        }
        if not any(option.strategy_type in safe_types for option in result.options):
            raise _semantic_error("high commitment risk requires a lower-risk option")
        selected = next(
            (
                option
                for option in result.options
                if option.option_id == result.recommended_option_id
            ),
            None,
        )
        if selected and selected.reply_constraints.commitment_level is CommitmentLevel.EXPLICIT:
            raise _semantic_error("high commitment risk cannot recommend explicit commitment")

    actual_types = {option.strategy_type for option in result.options}
    requires_risk_reduction = any(
        risk.confidence is Confidence.HIGH
        and risk.risk_type
        in {
            RiskType.RESPONSIBILITY,
            RiskType.COMMITMENT,
            RiskType.IRREVERSIBLE_ACTION,
        }
        for risk in event.risks
    )
    if requires_risk_reduction and StrategyType.RISK_REDUCTION not in actual_types:
        raise _semantic_error("high material risk requires a risk_reduction option")
    if any(
        risk.confidence is Confidence.HIGH
        and risk.risk_type is RiskType.IRREVERSIBLE_ACTION
        for risk in event.risks
    ) and StrategyType.CLARIFY not in actual_types:
        raise _semantic_error("irreversible action risk requires a clarify option")

    goal = request.user_goal.content if request.user_goal else ""
    decline_goal = any(marker in goal for marker in ("不答应", "拒绝"))
    relationship_goal = any(marker in goal for marker in ("关系", "合作"))
    if (
        decline_goal
        and relationship_goal
        and not {StrategyType.DECLINE, StrategyType.BOUNDARY} <= actual_types
    ):
        raise _semantic_error(
            "decline while preserving relationship requires decline and boundary"
        )
    if (
        unresolved
        and any(marker in goal for marker in ("推进", "完成", "解决"))
        and StrategyType.PROGRESS not in actual_types
    ):
        raise _semantic_error("progress goal with conflict requires a progress option")


def _validate_prohibited_output(result: StrategizeResult) -> None:
    option_text = "\n".join(
        option.model_dump_json(exclude={"option_id"}) for option in result.options
    )
    prohibited = {
        "对方是控制狂": "personality judgment",
        "对方是自恋型人格": "personality diagnosis",
        "对方是坏人": "personality judgment",
        "PUA型人格": "personality diagnosis",
        "你可以回复": "final reply generation",
        "可以直接回复": "final reply generation",
        '回复：“': "final reply generation",
    }
    for phrase, category in prohibited.items():
        if phrase in option_text:
            raise _semantic_error(f"result contains prohibited {category}")


def _semantic_error(message: str) -> StrategizeError:
    return StrategizeError(StrategizeErrorCode.SEMANTIC_VALIDATION_FAILED, message)
