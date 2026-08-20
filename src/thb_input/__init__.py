"""Embeddable THB meaning-only workflow."""

from thb_input.config import Settings as THBConfig
from thb_input.meaning import MeaningResult as THBResult
from thb_input.workflow import THBState, THBWorkflow, WorkflowError

__version__ = "0.1.0"


def THB(
    source_message: str,
    context: str | None = None,
    *,
    config: THBConfig | None = None,
) -> THBResult:
    return THBWorkflow(config=config).run(source_message, context)


__all__ = [
    "THB",
    "THBConfig",
    "THBResult",
    "THBState",
    "THBWorkflow",
    "WorkflowError",
    "__version__",
]
