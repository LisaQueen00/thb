from enum import StrEnum


class StrategizeErrorCode(StrEnum):
    LLM_CALL_FAILED = "LLM_CALL_FAILED"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_CONFIGURATION_ERROR = "LLM_CONFIGURATION_ERROR"
    INVALID_STRUCTURED_OUTPUT = "INVALID_STRUCTURED_OUTPUT"
    SCHEMA_VALIDATION_FAILED = "SCHEMA_VALIDATION_FAILED"
    SEMANTIC_VALIDATION_FAILED = "SEMANTIC_VALIDATION_FAILED"


class StrategizeError(Exception):
    def __init__(self, code: StrategizeErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
