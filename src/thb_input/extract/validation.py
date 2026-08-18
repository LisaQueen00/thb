import re
from collections.abc import Iterable

from pydantic import BaseModel, ValidationError

from thb_input.extract.errors import ExtractError, ExtractErrorCode
from thb_input.extract.schemas import (
    EpistemicStatus,
    EvidenceSource,
    ExtractResult,
)
from thb_input.schemas.input import InputRecord
from thb_input.strip.schemas import StripResult
from thb_input.strip.validation import validate_semantics as validate_strip_semantics


def validate_upstream(record: InputRecord, strip_result: StripResult) -> None:
    try:
        validate_strip_semantics(strip_result, record.source_message)
    except Exception as exc:
        raise ExtractError(
            ExtractErrorCode.EVIDENCE_VALIDATION_FAILED,
            "Strip Result is not consistent with canonical source_message",
        ) from exc


def validate_schema(payload: object) -> ExtractResult:
    try:
        return ExtractResult.model_validate(payload)
    except ValidationError as exc:
        raise ExtractError(
            ExtractErrorCode.SCHEMA_VALIDATION_FAILED,
            f"Extract result does not match the schema: {exc}",
        ) from exc


def validate_result(
    result: ExtractResult, record: InputRecord, strip_result: StripResult
) -> ExtractResult:
    validate_semantics(result, record)
    validate_evidence(result, record, strip_result)
    return result


def validate_semantics(result: ExtractResult, record: InputRecord) -> None:
    text = result.model_dump_json()
    prohibited = {
        "自恋型人格": "personality diagnosis",
        "控制狂": "personality judgment",
        "PUA型人格": "personality diagnosis",
        "用户应该拒绝": "strategy recommendation",
        "用户应该接受": "strategy recommendation",
        "你可以回复": "reply generation",
        '回复：“': "reply generation",
    }
    for phrase, category in prohibited.items():
        if phrase in text:
            raise _semantic_error(f"result contains prohibited {category}")

    for item in _epistemic_items(result):
        source = item.source
        status = getattr(item, "epistemic_status", None)
        if source is EvidenceSource.OTHER and status in {
            EpistemicStatus.REPORTED_BY_USER,
            EpistemicStatus.SUPPORTED_BY_BOTH,
        }:
            raise _semantic_error("other-sourced item has incompatible epistemic status")
        if source is EvidenceSource.USER_CONTEXT and status in {
            EpistemicStatus.REPORTED_BY_OTHER,
            EpistemicStatus.SUPPORTED_BY_BOTH,
        }:
            raise _semantic_error("context-sourced item has incompatible epistemic status")
        if source is EvidenceSource.USER_CONTEXT and record.context is None:
            raise _semantic_error("user_context source is impossible without USER_CONTEXT")
        if source is EvidenceSource.BOTH and status is not EpistemicStatus.SUPPORTED_BY_BOTH:
            raise _semantic_error("source=both requires epistemic_status=supported_by_both")
        if source is EvidenceSource.BOTH and record.context is None:
            raise _semantic_error("source=both is impossible without USER_CONTEXT")

    evidence_text = record.source_message + "\n" + (record.context or "")
    for constraint in result.time_constraints:
        if not _time_expression_is_grounded(constraint.expression, evidence_text):
            raise _semantic_error("time constraint expression is not present in current input")

    if any(conflict.resolution == "unresolved" for conflict in result.conflicts):
        conflict_markers = ("冲突", "不一致", "不同", "争议", "无法确定", "未解决")
        if not any(marker in result.event_summary for marker in conflict_markers):
            raise _semantic_error("event_summary omits an unresolved conflict")

    certainty_upgrades = ("对方的真实意图是", "对方一定想", "对方就是想")
    if any(phrase in result.event_summary for phrase in certainty_upgrades):
        raise _semantic_error("event_summary upgrades possible intention to certainty")

    _validate_unique_ids(result)


def validate_evidence(
    result: ExtractResult, record: InputRecord, strip_result: StripResult
) -> None:
    valid_ids = {segment.segment_id for segment in strip_result.segments}
    for item in _objects_with_evidence(result):
        references = item.supporting_segments
        if len(references) != len(set(references)):
            raise _evidence_error("supporting_segments contains duplicate IDs")
        invalid = set(references) - valid_ids
        if invalid:
            raise _evidence_error(f"unknown supporting segment IDs: {sorted(invalid)}")
        source = getattr(item, "source", None)
        if source is EvidenceSource.OTHER and not references:
            raise _evidence_error("other-sourced evidence must cite a Strip segment")
        if source is EvidenceSource.USER_CONTEXT and references:
            raise _evidence_error("context-only evidence cannot cite Strip segments")
        if source is EvidenceSource.BOTH and (record.context is None or not references):
            raise _evidence_error("source=both requires context and Strip evidence")


def _objects_with_evidence(result: ExtractResult) -> Iterable[BaseModel]:
    direct_fields = (
        "participants",
        "claims",
        "requests",
        "commitments",
        "time_constraints",
        "responsibilities",
        "conditions_and_consequences",
        "event_relationships",
        "presuppositions",
        "implicit_meanings",
        "possible_intentions",
        "risks",
    )
    for field in direct_fields:
        yield from getattr(result, field)
    for conflict in result.conflicts:
        yield from conflict.positions


def _epistemic_items(result: ExtractResult) -> Iterable[BaseModel]:
    for field in (
        "participants",
        "claims",
        "commitments",
        "time_constraints",
        "responsibilities",
        "conditions_and_consequences",
    ):
        yield from getattr(result, field)


def _validate_unique_ids(result: ExtractResult) -> None:
    id_fields = {
        "participants": "participant_id",
        "claims": "claim_id",
        "requests": "request_id",
        "commitments": "commitment_id",
        "time_constraints": "time_id",
        "responsibilities": "responsibility_id",
        "conditions_and_consequences": "relation_id",
        "event_relationships": "relationship_id",
        "presuppositions": "presupposition_id",
        "implicit_meanings": "implicit_id",
        "possible_intentions": "intention_id",
        "conflicts": "conflict_id",
        "unknowns": "unknown_id",
        "risks": "risk_id",
    }
    for collection, id_field in id_fields.items():
        ids = [getattr(item, id_field) for item in getattr(result, collection)]
        if len(ids) != len(set(ids)):
            raise _semantic_error(f"{collection} contains duplicate IDs")
        if ids:
            prefix = ids[0].rsplit("_", 1)[0]
            expected = [f"{prefix}_{index:03d}" for index in range(1, len(ids) + 1)]
            if ids != expected:
                raise _semantic_error(f"{collection} IDs must be sequential from 001")


_TIME_TOKEN = re.compile(
    r"\d{1,2}:\d{2}|(?:上午|中午|下午|晚上)?[一二三四五六七八九十两\d]{1,3}点(?:半)?|"
    r"今天|今日|明天|明日|昨天|昨日|本周|下周|上周|周[一二三四五六日天]|"
    r"上午|中午|下午|晚上|月底|月初|年底|尽快"
)


def _time_expression_is_grounded(expression: str, evidence_text: str) -> bool:
    if expression in evidence_text:
        return True
    tokens = _TIME_TOKEN.findall(expression)
    return bool(tokens) and all(token in evidence_text for token in tokens)

def _semantic_error(message: str) -> ExtractError:
    return ExtractError(ExtractErrorCode.SEMANTIC_VALIDATION_FAILED, message)


def _evidence_error(message: str) -> ExtractError:
    return ExtractError(ExtractErrorCode.EVIDENCE_VALIDATION_FAILED, message)
