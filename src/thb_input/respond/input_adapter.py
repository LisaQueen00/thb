from dataclasses import dataclass

from thb_input.respond.schemas import RespondRequest


@dataclass(frozen=True)
class RespondModelInput:
    selected_strategy: dict[str, object]
    relevant_event_context: dict[str, object]


def adapt_input(request: RespondRequest) -> RespondModelInput:
    """Expose only the selected strategy and reply-relevant facts."""
    return RespondModelInput(
        selected_strategy=request.selected_strategy.model_dump(mode="json"),
        relevant_event_context=request.relevant_event_context.model_dump(mode="json"),
    )
