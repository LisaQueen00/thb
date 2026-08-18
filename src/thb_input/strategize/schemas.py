from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from thb_input.extract.schemas import ExtractResult


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserGoalSource(StrEnum):
    EXPLICIT = "explicit_user_input"
    DEFAULT = "default_options"


class UserGoalInput(StrictModel):
    content: str = Field(min_length=1)


class ResolvedUserGoal(StrictModel):
    source: UserGoalSource
    content: str | None


class StrategizeRequest(StrictModel):
    extract_result: ExtractResult
    user_goal: UserGoalInput | None = None
    context: str | None = None


class StrategyType(StrEnum):
    PROGRESS = "progress"
    CLARIFY = "clarify"
    BOUNDARY = "boundary"
    RISK_REDUCTION = "risk_reduction"
    DELAY_AND_VERIFY = "delay_and_verify"
    DECLINE = "decline"


class Tone(StrEnum):
    NEUTRAL = "neutral"
    WARM = "warm"
    FIRM = "firm"
    CONCISE = "concise"


class BoundaryLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CommitmentLevel(StrEnum):
    NONE = "none"
    LIMITED = "limited"
    EXPLICIT = "explicit"


class StrategyContext(StrictModel):
    key_conflicts: list[str]
    key_unknowns: list[str]
    key_risks: list[str]


class RequiredUserInput(StrictModel):
    field: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class ReplyConstraints(StrictModel):
    must_include: list[str]
    must_not_include: list[str]
    tone: Tone
    boundary_level: BoundaryLevel
    commitment_level: CommitmentLevel


class StrategyOption(StrictModel):
    option_id: str = Field(pattern=r"^strategy_\d{3,}$")
    strategy_type: StrategyType
    title: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    key_actions: list[str] = Field(min_length=1)
    what_to_accept: list[str]
    what_not_to_accept: list[str]
    clarification_needed: list[str]
    benefits: list[str] = Field(min_length=1)
    tradeoffs: list[str] = Field(min_length=1)
    risks: list[str]
    prerequisites: list[str]
    reply_constraints: ReplyConstraints


class StrategizeResult(StrictModel):
    strategy_version: Literal["0.1"]
    user_goal: ResolvedUserGoal
    strategy_context: StrategyContext
    required_user_input: list[RequiredUserInput]
    options: list[StrategyOption] = Field(min_length=2, max_length=4)
    recommended_option_id: str | None
    custom_strategy_supported: Literal[True]
