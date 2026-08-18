from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from thb_input.extract.schemas import ExtractResult
from thb_input.respond.schemas import RespondResult
from thb_input.strategize.schemas import StrategyOption


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OutputRequest(StrictModel):
    extract_result: ExtractResult
    selected_strategy: StrategyOption
    respond_result: RespondResult


class PlainLanguage(StrictModel):
    content: str = Field(min_length=1)


class CounterpartyRequest(StrictModel):
    actions: list[str]
    requested_time: list[str]
    conditions: list[str]
    claimed_consequences: list[str]


class EventLogic(StrictModel):
    current_state: list[str]
    prior_events: list[str]
    current_requests: list[str]
    time_logic: list[str]
    responsibility_logic: list[str]
    dependencies: list[str]
    conflicts: list[str]
    unknowns: list[str]


class StrategyDisplay(StrictModel):
    strategy_option_id: str = Field(pattern=r"^strategy_\d{3,}$")
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    key_actions: list[str]


class ReplyDisplay(StrictModel):
    content: str = Field(min_length=1)
    copyable: Literal[True]


class OutputResult(StrictModel):
    output_version: Literal["0.1"]
    plain_language: PlainLanguage
    counterparty_request: CounterpartyRequest
    event_logic: EventLogic
    attention: list[str] = Field(max_length=3)
    strategy: StrategyDisplay
    reply: ReplyDisplay
