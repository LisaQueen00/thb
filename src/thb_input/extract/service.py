import logging
import time

from thb_input.extract.errors import ExtractError, ExtractErrorCode
from thb_input.extract.input_adapter import adapt_input
from thb_input.extract.llm import ExtractLLMClient
from thb_input.extract.parser import parse_model_response
from thb_input.extract.prompt import build_extract_prompt, build_extract_retry_prompt
from thb_input.extract.schemas import ExtractRequest, ExtractResult
from thb_input.extract.validation import validate_result, validate_schema, validate_upstream

logger = logging.getLogger(__name__)


class ExtractService:
    def __init__(self, llm_client: ExtractLLMClient, validation_retries: int = 1) -> None:
        self.llm_client = llm_client
        self.validation_retries = validation_retries

    def process(self, request: ExtractRequest) -> ExtractResult:
        started_at = time.perf_counter()
        validate_upstream(request.canonical_input, request.strip_result)
        prompt = build_extract_prompt(
            adapt_input(request.canonical_input, request.strip_result)
        )
        retryable = {
            ExtractErrorCode.INVALID_STRUCTURED_OUTPUT,
            ExtractErrorCode.SCHEMA_VALIDATION_FAILED,
            ExtractErrorCode.SEMANTIC_VALIDATION_FAILED,
            ExtractErrorCode.EVIDENCE_VALIDATION_FAILED,
        }
        for attempt in range(self.validation_retries + 1):
            try:
                payload = parse_model_response(self.llm_client.complete_structured(prompt))
                result = validate_schema(payload)
                validate_result(
                    result,
                    request.canonical_input,
                    request.strip_result,
                )
                logger.info(
                    "extract_completed attempts=%d elapsed_ms=%d claims=%d risks=%d",
                    attempt + 1,
                    int((time.perf_counter() - started_at) * 1000),
                    len(result.claims),
                    len(result.risks),
                )
                return result
            except ExtractError as exc:
                if exc.code not in retryable or attempt >= self.validation_retries:
                    logger.warning(
                        "extract_failed attempts=%d elapsed_ms=%d error_code=%s",
                        attempt + 1,
                        int((time.perf_counter() - started_at) * 1000),
                        exc.code.value,
                    )
                    raise
                prompt = build_extract_retry_prompt(prompt, exc.code.value, exc.message)
        raise RuntimeError("unreachable Extract validation retry state")
