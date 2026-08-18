from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from thb_input.strategize.schemas import (
    BoundaryLevel,
    CommitmentLevel,
    StrategyOption,
    Tone,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RelevantEventContext(StrictModel):
    event_summary: str = Field(min_length=1)
    relevant_participants: list[str] = Field(default_factory=list)
    relevant_requests: list[str] = Field(default_factory=list)
    relevant_time_constraints: list[str] = Field(default_factory=list)


class RespondRequest(StrictModel):
    selected_strategy: StrategyOption
    relevant_event_context: RelevantEventContext


class AppliedConstraints(StrictModel):
    tone: Tone
    boundary_level: BoundaryLevel
    commitment_level: CommitmentLevel


class RespondResult(StrictModel):
    respond_version: Literal["0.1"]
    strategy_option_id: str = Field(pattern=r"^strategy_\d{3,}$")
    reply: str = Field(min_length=1)
    applied_constraints: AppliedConstraints

    @model_validator(mode="after")
    def strip_is_not_a_reply(self) -> "RespondResult":
        if not self.reply.strip():
            raise ValueError("reply must contain visible text")
        return self
