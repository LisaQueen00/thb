import logging
import time

from thb_input.strategize.errors import StrategizeError, StrategizeErrorCode
from thb_input.strategize.input_adapter import adapt_input
from thb_input.strategize.llm import StrategizeLLMClient
from thb_input.strategize.parser import parse_model_response
from thb_input.strategize.prompt import (
    build_strategize_prompt,
    build_strategize_retry_prompt,
)
from thb_input.strategize.schemas import StrategizeRequest, StrategizeResult
from thb_input.strategize.validation import validate_schema, validate_semantics

logger = logging.getLogger(__name__)


class StrategizeService:
    def __init__(self, llm_client: StrategizeLLMClient, validation_retries: int = 2) -> None:
        self.llm_client = llm_client
        self.validation_retries = validation_retries

    def process(self, request: StrategizeRequest) -> StrategizeResult:
        started_at = time.perf_counter()
        prompt = build_strategize_prompt(adapt_input(request))
        retryable = {
            StrategizeErrorCode.INVALID_STRUCTURED_OUTPUT,
            StrategizeErrorCode.SCHEMA_VALIDATION_FAILED,
            StrategizeErrorCode.SEMANTIC_VALIDATION_FAILED,
        }
        for attempt in range(self.validation_retries + 1):
            try:
                payload = parse_model_response(self.llm_client.complete_structured(prompt))
                result = validate_schema(payload)
                validate_semantics(result, request)
                logger.info(
                    "strategize_completed attempts=%d elapsed_ms=%d options=%d",
                    attempt + 1,
                    int((time.perf_counter() - started_at) * 1000),
                    len(result.options),
                )
                return result
            except StrategizeError as exc:
                if exc.code not in retryable or attempt >= self.validation_retries:
                    logger.warning(
                        "strategize_failed attempts=%d elapsed_ms=%d error_code=%s",
                        attempt + 1,
                        int((time.perf_counter() - started_at) * 1000),
                        exc.code.value,
                    )
                    raise
                prompt = build_strategize_retry_prompt(
                    prompt,
                    exc.code.value,
                    exc.message,
                )
        raise RuntimeError("unreachable Strategize validation retry state")
