from pydantic import ValidationError

from thb_input.strip.errors import StripError, StripErrorCode
from thb_input.strip.schemas import (
    StripModelResult,
    StripResult,
    StripSegment,
    StripSummary,
)
from thb_input.strip.taxonomy import EVALUATIVE_LABELS, IMPLICIT_LABELS, PRESSURE_LABELS


def validate_schema(payload: object) -> StripResult:
    try:
        return StripResult.model_validate(payload)
    except ValidationError as exc:
        raise StripError(
            StripErrorCode.SCHEMA_VALIDATION_FAILED,
            f"Strip result does not match the schema: {exc}",
        ) from exc


def validate_model_schema(payload: object) -> StripModelResult:
    try:
        return StripModelResult.model_validate(payload)
    except ValidationError as exc:
        raise StripError(
            StripErrorCode.SCHEMA_VALIDATION_FAILED,
            f"Model annotation does not match the schema: {exc}",
        ) from exc


def materialize_strip_result(
    annotation: StripModelResult, source_message: str
) -> StripResult:
    segments = [
        StripSegment(
            segment_id=f"seg_{index:03d}",
            text=segment.text,
            labels=segment.labels,
        )
        for index, segment in enumerate(annotation.segments, start=1)
    ]
    labels = list(
        dict.fromkeys(label for segment in annotation.segments for label in segment.labels)
    )
    label_set = set(labels)
    result = StripResult(
        strip_version="0.1",
        segments=segments,
        summary=StripSummary(
            detected_labels=labels,
            contains_implicit_language=bool(label_set & IMPLICIT_LABELS),
            contains_pressure_language=bool(label_set & PRESSURE_LABELS),
            contains_evaluative_language=bool(label_set & EVALUATIVE_LABELS),
        ),
    )
    return validate_semantics(result, source_message)


def validate_semantics(result: StripResult, source_message: str) -> StripResult:
    ids = [segment.segment_id for segment in result.segments]
    if len(ids) != len(set(ids)):
        raise _semantic_error("segment_id values must be unique")

    expected_ids = [f"seg_{index:03d}" for index in range(1, len(ids) + 1)]
    if ids != expected_ids:
        raise _semantic_error("segment_id values must be sequential from seg_001")

    cursor = 0
    for segment in result.segments:
        if len(segment.labels) != len(set(segment.labels)):
            raise _semantic_error(f"segment {segment.segment_id} contains duplicate labels")
        position = source_message.find(segment.text, cursor)
        if position < 0:
            raise _semantic_error(
                f"segment {segment.segment_id} is not traceable to source_message in order"
            )
        if source_message[cursor:position].strip():
            raise _semantic_error(
                f"source content before {segment.segment_id} was omitted from segmentation"
            )
        cursor = position + len(segment.text)

    if source_message[cursor:].strip():
        raise _semantic_error("source content after the final segment was omitted")

    segment_labels = {
        label for segment in result.segments for label in segment.labels
    }
    summary_labels = set(result.summary.detected_labels)
    if len(result.summary.detected_labels) != len(summary_labels):
        raise _semantic_error("summary.detected_labels contains duplicates")
    if summary_labels != segment_labels:
        raise _semantic_error("summary.detected_labels must equal the labels used by segments")

    expected_flags = {
        "contains_implicit_language": bool(segment_labels & IMPLICIT_LABELS),
        "contains_pressure_language": bool(segment_labels & PRESSURE_LABELS),
        "contains_evaluative_language": bool(segment_labels & EVALUATIVE_LABELS),
    }
    for field, expected in expected_flags.items():
        if getattr(result.summary, field) is not expected:
            raise _semantic_error(f"summary.{field} is inconsistent with segment labels")

    return result


def _semantic_error(message: str) -> StripError:
    return StripError(StripErrorCode.SEMANTIC_VALIDATION_FAILED, message)
