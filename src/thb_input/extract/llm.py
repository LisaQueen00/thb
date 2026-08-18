from typing import Protocol

from thb_input.config import Settings
from thb_input.extract.errors import ExtractError, ExtractErrorCode
from thb_input.extract.prompt import ExtractPrompt
from thb_input.strip.errors import StripError, StripErrorCode
from thb_input.strip.llm import OpenAICompatibleLLMClient


class ExtractLLMClient(Protocol):
    def complete_structured(self, prompt: ExtractPrompt) -> object: ...


class OpenAICompatibleExtractLLMClient:
    """Extract configuration over the shared provider implementation."""

    def __init__(self, settings: Settings) -> None:
        model = settings.extract_model or settings.strip_model
        if not model:
            self.client = None
            return
        provider_settings = settings.model_copy(
            update={
                "strip_model": model,
                "strip_temperature": settings.extract_temperature,
                "strip_max_tokens": settings.extract_max_tokens,
                "strip_output_mode": settings.extract_output_mode,
                "llm_timeout": settings.extract_timeout,
            }
        )
        self.client = OpenAICompatibleLLMClient(
            provider_settings,
            schema_name="thb_extract_result",
        )

    def complete_structured(self, prompt: ExtractPrompt) -> object:
        if self.client is None:
            raise ExtractError(
                ExtractErrorCode.LLM_CONFIGURATION_ERROR,
                "THB_EXTRACT_MODEL is not configured",
            )
        try:
            return self.client.complete_structured(prompt)
        except StripError as exc:
            mapping = {
                StripErrorCode.LLM_CALL_FAILED: ExtractErrorCode.LLM_CALL_FAILED,
                StripErrorCode.LLM_TIMEOUT: ExtractErrorCode.LLM_TIMEOUT,
                StripErrorCode.LLM_CONFIGURATION_ERROR: (
                    ExtractErrorCode.LLM_CONFIGURATION_ERROR
                ),
                StripErrorCode.INVALID_STRUCTURED_OUTPUT: (
                    ExtractErrorCode.INVALID_STRUCTURED_OUTPUT
                ),
            }
            raise ExtractError(
                mapping.get(exc.code, ExtractErrorCode.LLM_CALL_FAILED),
                exc.message,
            ) from exc
