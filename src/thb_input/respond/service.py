import logging
import time

from thb_input.respond.errors import RespondError, RespondErrorCode
from thb_input.respond.input_adapter import adapt_input
from thb_input.respond.llm import RespondLLMClient
from thb_input.respond.parser import parse_model_response
from thb_input.respond.prompt import build_respond_prompt, build_respond_retry_prompt
from thb_input.respond.schemas import RespondRequest, RespondResult
from thb_input.respond.validation import validate_schema, validate_semantics

logger = logging.getLogger(__name__)


class RespondService:
    def __init__(self, llm_client: RespondLLMClient, validation_retries: int = 2) -> None:
        self.llm_client = llm_client
        self.validation_retries = validation_retries

    def process(self, request: RespondRequest) -> RespondResult:
        started_at = time.perf_counter()
        prompt = build_respond_prompt(adapt_input(request))
        retryable = {
            RespondErrorCode.INVALID_STRUCTURED_OUTPUT,
            RespondErrorCode.SCHEMA_VALIDATION_FAILED,
            RespondErrorCode.CONSTRAINT_VALIDATION_FAILED,
            RespondErrorCode.SEMANTIC_VALIDATION_FAILED,
        }
        for attempt in range(self.validation_retries + 1):
            try:
                payload = parse_model_response(self.llm_client.complete_structured(prompt))
                result = validate_schema(payload)
                validate_semantics(result, request)
                logger.info(
                    "respond_completed attempts=%d elapsed_ms=%d reply_chars=%d",
                    attempt + 1,
                    int((time.perf_counter() - started_at) * 1000),
                    len(result.reply),
                )
                return result
            except RespondError as exc:
                if exc.code not in retryable or attempt >= self.validation_retries:
                    logger.warning(
                        "respond_failed attempts=%d elapsed_ms=%d error_code=%s",
                        attempt + 1,
                        int((time.perf_counter() - started_at) * 1000),
                        exc.code.value,
                    )
                    raise
                prompt = build_respond_retry_prompt(prompt, exc.code.value, exc.message)
        raise RuntimeError("unreachable Respond validation retry state")
