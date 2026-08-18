from typing import Protocol

from thb_input.config import Settings
from thb_input.strategize.errors import StrategizeError, StrategizeErrorCode
from thb_input.strategize.prompt import StrategizePrompt
from thb_input.strip.errors import StripError, StripErrorCode
from thb_input.strip.llm import OpenAICompatibleLLMClient


class StrategizeLLMClient(Protocol):
    def complete_structured(self, prompt: StrategizePrompt) -> object: ...


class OpenAICompatibleStrategizeLLMClient:
    """Strategize configuration over the shared provider implementation."""

    def __init__(self, settings: Settings) -> None:
        model = settings.strategize_model or settings.extract_model or settings.strip_model
        if not model:
            self.client = None
            return
        provider_settings = settings.model_copy(
            update={
                "strip_model": model,
                "strip_temperature": settings.strategize_temperature,
                "strip_max_tokens": settings.strategize_max_tokens,
                "strip_output_mode": settings.strategize_output_mode,
                "llm_timeout": settings.strategize_timeout,
            }
        )
        self.client = OpenAICompatibleLLMClient(
            provider_settings,
            schema_name="thb_strategize_result",
        )

    def complete_structured(self, prompt: StrategizePrompt) -> object:
        if self.client is None:
            raise StrategizeError(
                StrategizeErrorCode.LLM_CONFIGURATION_ERROR,
                "THB_STRATEGIZE_MODEL is not configured",
            )
        try:
            return self.client.complete_structured(prompt)
        except StripError as exc:
            mapping = {
                StripErrorCode.LLM_CALL_FAILED: StrategizeErrorCode.LLM_CALL_FAILED,
                StripErrorCode.LLM_TIMEOUT: StrategizeErrorCode.LLM_TIMEOUT,
                StripErrorCode.LLM_CONFIGURATION_ERROR: (
                    StrategizeErrorCode.LLM_CONFIGURATION_ERROR
                ),
                StripErrorCode.INVALID_STRUCTURED_OUTPUT: (
                    StrategizeErrorCode.INVALID_STRUCTURED_OUTPUT
                ),
            }
            raise StrategizeError(
                mapping.get(exc.code, StrategizeErrorCode.LLM_CALL_FAILED),
                exc.message,
            ) from exc
