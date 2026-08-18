from dataclasses import dataclass

from thb_input.schemas.input import InputRecord
from thb_input.strip.schemas import StripResult


@dataclass(frozen=True)
class ExtractModelInput:
    source_message: str
    context: str | None
    source_metadata: dict[str, object]
    unknown_fields: list[str]
    input_security: dict[str, object]
    strip_result: dict[str, object]


def adapt_input(record: InputRecord, strip_result: StripResult) -> ExtractModelInput:
    """Apply minimum context while keeping canonical and Strip sources distinct."""
    return ExtractModelInput(
        source_message=record.source_message,
        context=record.context,
        source_metadata=record.source_metadata.model_dump(mode="json"),
        unknown_fields=record.unknown_fields,
        input_security={
            "content_role": record.input_handling.content_role,
            "instructions_executable": record.input_handling.instructions_executable,
            "prompt_injection_detected": record.input_handling.prompt_injection_detected,
        },
        strip_result=strip_result.model_dump(mode="json"),
    )
