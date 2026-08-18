import json
import re
import unicodedata

from pydantic import ValidationError

from thb_input.respond.errors import RespondError, RespondErrorCode
from thb_input.respond.schemas import RespondRequest, RespondResult
from thb_input.strategize.schemas import CommitmentLevel, StrategyType


def validate_schema(payload: object) -> RespondResult:
    try:
        return RespondResult.model_validate(payload)
    except ValidationError as exc:
        raise RespondError(
            RespondErrorCode.SCHEMA_VALIDATION_FAILED,
            f"Respond result does not match the schema: {exc}",
        ) from exc


def validate_semantics(result: RespondResult, request: RespondRequest) -> RespondResult:
    strategy = request.selected_strategy
    expected = strategy.reply_constraints
    if result.strategy_option_id != strategy.option_id:
        raise _constraint("strategy_option_id does not match the selected strategy")
    if (
        result.applied_constraints.tone is not expected.tone
        or result.applied_constraints.boundary_level is not expected.boundary_level
        or result.applied_constraints.commitment_level is not expected.commitment_level
    ):
        raise _constraint("applied_constraints do not match the selected strategy")

    reply = _normalize(result.reply)
    _validate_must_include(reply, expected.must_include)
    _validate_prohibited_meaning(reply, expected.must_not_include + strategy.what_not_to_accept)
    _validate_commitment(reply, expected.commitment_level)
    _validate_strategy(reply, strategy.strategy_type)
    _validate_safety_and_leakage(reply)
    _validate_fact_tokens(result.reply, request)
    return result


def _validate_must_include(reply: str, requirements: list[str]) -> None:
    missing = [item for item in requirements if not _meaning_is_covered(reply, item)]
    if missing:
        raise _constraint(f"reply does not cover must_include: {missing!r}")


def _meaning_is_covered(reply: str, requirement: str) -> bool:
    required = _normalize(requirement)
    if required in reply:
        return True
    # Deterministic semantic approximation: all meaningful clauses/terms must occur.
    tokens = [
        token for token in re.split(r"[，,。；;：:\s]|并且|以及|同时", required) if len(token) >= 2
    ]
    return bool(tokens) and all(token in reply for token in tokens)


def _validate_prohibited_meaning(reply: str, prohibited: list[str]) -> None:
    violations = [item for item in prohibited if _prohibited_is_expressed(reply, item)]
    if violations:
        raise _constraint(f"reply expresses prohibited meaning: {violations!r}")


def _prohibited_is_expressed(reply: str, item: str) -> bool:
    normalized = _normalize(item)
    if normalized in reply:
        return True
    # Catch the common contract form “不要/不得/不能/避免 X” as X itself.
    core = re.sub(r"^(不要|不得|不能|避免|不应|不承认|不接受)", "", normalized)
    core = re.sub(r"^(承认|表达|声称|承诺)", "", core)
    if len(core) >= 4 and core in reply:
        return True
    # High-risk admissions need concept-level checks because a model may paraphrase them.
    if "今天" in normalized and any(
        marker in normalized for marker in ("答应", "约定", "期限", "deadline")
    ):
        deadline_admission = (
            r"(?:之前|此前|原来|原本)?(?:答应|说好|约定).{0,8}今天",
            r"今天.{0,8}(?:约定|原定|既定|截止|期限|交付日)",
        )
        if any(re.search(pattern, reply) for pattern in deadline_admission):
            return True
    if "责任" in normalized and any(
        marker in normalized for marker in ("全部", "所有", "用户", "我")
    ):
        responsibility_admission = (
            r"(?:全部|所有|后续).{0,8}(?:责任|问题).{0,8}(?:我负责|由我承担)",
            r"(?:我负责|由我承担).{0,8}(?:全部|所有|后续)",
            r"出了?问题.{0,8}我(?:来)?负责",
        )
        if any(re.search(pattern, reply) for pattern in responsibility_admission):
            return True
    return False


def _validate_commitment(reply: str, level: CommitmentLevel) -> None:
    strong = (
        "保证",
        "一定完成",
        "肯定完成",
        "确保完成",
        "全权负责",
        "承担全部",
        "绝对不会",
        "我答应",
        "我承诺",
    )
    if level is not CommitmentLevel.EXPLICIT and any(item in reply for item in strong):
        raise _constraint("reply introduces a commitment beyond commitment_level")
    if level is CommitmentLevel.NONE:
        patterns = (r"我会在[^，。！？]{0,20}(完成|交付|付款|解决)", r"我会负责")
        if any(re.search(pattern, reply) for pattern in patterns):
            raise _constraint("reply introduces a commitment while commitment_level is none")


def _validate_strategy(reply: str, strategy_type: StrategyType) -> None:
    if strategy_type is StrategyType.CLARIFY:
        unsupported_certainty = ("已经确认", "就按这个期限", "一定完成", "肯定完成")
        if any(item in reply for item in unsupported_certainty):
            raise _semantic("clarify strategy was converted into a factual commitment")


def _validate_safety_and_leakage(reply: str) -> None:
    attacks = ("你就是个", "你这种人", "人格有问题", "控制狂", "自恋型人格", "脑子有病")
    leakage = (
        "thb",
        "系统提示词",
        "模型判断",
        "风险分析",
        "selectedstrategy",
        "mustinclude",
        "mustnotinclude",
        "communicationbehavior",
        "presupposition",
    )
    if any(item in reply for item in attacks):
        raise _semantic("reply contains a personality attack or diagnosis")
    if any(item in reply for item in leakage):
        raise _semantic("reply leaks internal analysis or implementation details")
    canned = ("感谢您的理解与配合", "我们非常重视", "针对您反馈的问题")
    if sum(item in reply for item in canned) >= 2:
        raise _semantic("reply contains excessive customer-service boilerplate")
    if len(reply) > 600 or reply.count("\n") > 4:
        raise _semantic("reply is excessively long for a ready-to-send response")


def _validate_fact_tokens(reply: str, request: RespondRequest) -> None:
    source = json.dumps(request.model_dump(mode="json"), ensure_ascii=False)
    # New exact dates/times and money amounts are high-risk fabricated facts.
    patterns = (
        r"\d{4}[年/-]\d{1,2}[月/-]\d{1,2}日?",
        r"\d{1,2}[月/-]\d{1,2}日?",
        r"\d{1,2}[:：]\d{2}",
        r"(?:¥|￥)\s?\d+(?:\.\d+)?",
        r"\d+(?:\.\d+)?\s?元",
    )
    for pattern in patterns:
        for token in re.findall(pattern, reply):
            if token not in source:
                raise _semantic(f"reply introduces an unsupported concrete fact: {token}")


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower()
    return re.sub(r"[\s\"'“”‘’（）()<>《》]", "", value)


def _constraint(message: str) -> RespondError:
    return RespondError(RespondErrorCode.CONSTRAINT_VALIDATION_FAILED, message)


def _semantic(message: str) -> RespondError:
    return RespondError(RespondErrorCode.SEMANTIC_VALIDATION_FAILED, message)
