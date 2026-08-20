from .state import THBState


class WorkflowError(RuntimeError):
    def __init__(self, code: str, stage: str, message: str, state: THBState) -> None:
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.message = message
        self.state = state
