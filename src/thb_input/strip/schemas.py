from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from thb_input.strip.taxonomy import CommunicationLabel


class StripSegment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segment_id: str = Field(pattern=r"^seg_\d{3,}$")
    text: str = Field(min_length=1)
    labels: list[CommunicationLabel] = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("segment text must contain non-whitespace content")
        return value


class StripModelSegment(BaseModel):
    """Minimal annotation the LLM is responsible for producing."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    labels: list[CommunicationLabel] = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("segment text must contain non-whitespace content")
        return value


class StripModelResult(BaseModel):
    """Internal Structured Output contract sent to the model."""

    model_config = ConfigDict(extra="forbid")

    segments: list[StripModelSegment] = Field(min_length=1)


class StripSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detected_labels: list[CommunicationLabel] = Field(min_length=1)
    contains_implicit_language: bool
    contains_pressure_language: bool
    contains_evaluative_language: bool


class StripResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strip_version: Literal["0.1"]
    segments: list[StripSegment] = Field(min_length=1)
    summary: StripSummary
