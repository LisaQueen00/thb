import logging
import time

from thb_input.schemas.input import InputRecord
from thb_input.strip.errors import StripError, StripErrorCode
from thb_input.strip.input_adapter import adapt_input
from thb_input.strip.llm import LLMClient
from thb_input.strip.parser import parse_model_response
from thb_input.strip.prompt import build_strip_prompt, build_strip_retry_prompt
from thb_input.strip.schemas import StripResult
from thb_input.strip.validation import materialize_strip_result, validate_model_schema

logger = logging.getLogger(__name__)


class StripService:
    def __init__(self, llm_client: LLMClient, validation_retries: int = 1) -> None:
        self.llm_client = llm_client
        self.validation_retries = validation_retries

    def process(self, canonical_input: InputRecord) -> StripResult:
        started_at = time.perf_counter()
        model_input = adapt_input(canonical_input)
        prompt = build_strip_prompt(model_input)
        retryable_codes = {
            StripErrorCode.INVALID_STRUCTURED_OUTPUT,
            StripErrorCode.SCHEMA_VALIDATION_FAILED,
            StripErrorCode.SEMANTIC_VALIDATION_FAILED,
        }

        for attempt in range(self.validation_retries + 1):
            try:
                raw_response = self.llm_client.complete_structured(prompt)
                payload = parse_model_response(raw_response)
                annotation = validate_model_schema(payload)
                result = materialize_strip_result(
                    annotation, canonical_input.source_message
                )
                logger.info(
                    "strip_completed attempts=%d elapsed_ms=%d segments=%d",
                    attempt + 1,
                    int((time.perf_counter() - started_at) * 1000),
                    len(result.segments),
                )
                return result
            except StripError as exc:
                if exc.code not in retryable_codes or attempt >= self.validation_retries:
                    logger.warning(
                        "strip_failed attempts=%d elapsed_ms=%d error_code=%s",
                        attempt + 1,
                        int((time.perf_counter() - started_at) * 1000),
                        exc.code.value,
                    )
                    raise
                prompt = build_strip_retry_prompt(
                    prompt, exc.code.value, exc.message
                )

        raise RuntimeError("unreachable Strip validation retry state")
