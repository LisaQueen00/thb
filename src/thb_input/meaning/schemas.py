from pydantic import BaseModel, ConfigDict, Field


class MeaningResult(BaseModel):
    """The single user-facing semantic result of the THB workflow."""

    model_config = ConfigDict(extra="forbid")
    meaning: str = Field(min_length=1)
