from dataclasses import dataclass

from thb_input.schemas.input import InputRecord


@dataclass(frozen=True)
class StripModelInput:
    source_message: str
    context: str | None
    content_role: str
    instructions_executable: bool
    prompt_injection_detected: bool


def adapt_input(record: InputRecord) -> StripModelInput:
    """Apply the minimum-context principle without modifying canonical input."""
    return StripModelInput(
        source_message=record.source_message,
        context=record.context,
        content_role=record.input_handling.content_role,
        instructions_executable=record.input_handling.instructions_executable,
        prompt_injection_detected=record.input_handling.prompt_injection_detected,
    )

