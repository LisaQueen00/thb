from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from thb_input.extract.schemas import ExtractResult
from thb_input.meaning.schemas import MeaningResult
from thb_input.schemas.input import InputRecord
from thb_input.strip.schemas import StripResult


class WorkflowStage(StrEnum):
    CREATED = "created"
    INPUT = "input"
    STRIP = "strip"
    EXTRACT = "extract"
    MEANING = "meaning"


class WorkflowStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class THBState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state_version: str = "0.1"
    current_stage: WorkflowStage = WorkflowStage.CREATED
    status: WorkflowStatus = WorkflowStatus.RUNNING
    canonical_input: InputRecord | None = None
    strip_result: StripResult | None = None
    extract_result: ExtractResult | None = None
    meaning_result: MeaningResult | None = None
    stage_durations_ms: dict[str, float] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
