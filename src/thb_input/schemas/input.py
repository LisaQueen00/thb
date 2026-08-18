from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceType(StrEnum):
    PASTED_TEXT = "pasted_text"
    SCREENSHOT = "screenshot"


class CaptureMethod(StrEnum):
    PASTE = "paste"
    IMAGE_UNDERSTANDING = "image_understanding"


class Platform(StrEnum):
    WECHAT = "wechat"
    EMAIL = "email"
    OTHER = "other"
    UNKNOWN = "unknown"


class TextInputRequest(BaseModel):
    """Low-friction user input for pasted communication text."""

    model_config = ConfigDict(extra="forbid")

    source_message: str = Field(
        description="The other party's original words, preserved without rewriting."
    )
    context: str | None = Field(
        default=None,
        description="Optional background supplied separately by the user.",
    )

    @field_validator("source_message")
    @classmethod
    def source_message_must_contain_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source_message must contain non-whitespace text")
        return value

    @field_validator("context")
    @classmethod
    def context_must_contain_text_when_present(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("context must contain non-whitespace text when provided")
        return value


class SourceMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: SourceType
    capture_method: CaptureMethod
    platform: Platform
    participants: list[str]
    timestamp: datetime | None
    message_order_preserved: bool


class InputHandling(BaseModel):
    """Trust boundary consumed by later model-backed stages."""

    model_config = ConfigDict(extra="forbid")

    content_role: Literal["untrusted_data"] = "untrusted_data"
    instructions_executable: Literal[False] = False
    prompt_injection_detected: bool
    handling: Literal[
        "preserved_as_untrusted_data",
        "detected_but_preserved_as_data",
    ]
    detected_fields: list[Literal["source_message", "context"]]
    matched_rules: list[str]


class InputWarning(BaseModel):
    """Structured, machine-readable warning produced during input handling."""

    model_config = ConfigDict(extra="forbid")

    code: Literal["prompt_injection_detected"]
    severity: Literal["warning"] = "warning"
    fields: list[Literal["source_message", "context"]]
    rules: list[str]


class RawSourceReference(BaseModel):
    """Reference to retained original evidence; used by image input in a later stage."""

    model_config = ConfigDict(extra="forbid")

    reference: str
    media_type: str


class InputRecord(BaseModel):
    """Stable output contract handed to downstream THB modules."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["0.1"] = "0.1"
    source_message: str
    context: str | None
    source_metadata: SourceMetadata
    raw_source: RawSourceReference | None
    unknown_fields: list[str]
    warnings: list[InputWarning]
    input_handling: InputHandling
