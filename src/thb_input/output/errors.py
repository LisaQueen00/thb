from enum import StrEnum


class OutputErrorCode(StrEnum):
    INPUT_CONTRACT_MISMATCH = "INPUT_CONTRACT_MISMATCH"
    OUTPUT_VALIDATION_FAILED = "OUTPUT_VALIDATION_FAILED"


class OutputError(Exception):
    def __init__(self, code: OutputErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
