from dataclasses import dataclass

from thb_input.strategize.schemas import StrategizeRequest


@dataclass(frozen=True)
class StrategizeModelInput:
    event_model: dict[str, object]
    user_goal: str | None
    context: str | None


def adapt_input(request: StrategizeRequest) -> StrategizeModelInput:
    """Pass the validated Event Model without reopening raw-source analysis."""
    return StrategizeModelInput(
        event_model=request.extract_result.model_dump(mode="json"),
        user_goal=request.user_goal.content if request.user_goal else None,
        context=request.context,
    )
