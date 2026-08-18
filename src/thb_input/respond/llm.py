from typing import Protocol

from thb_input.config import Settings
from thb_input.respond.errors import RespondError, RespondErrorCode
from thb_input.respond.prompt import RespondPrompt
from thb_input.strip.errors import StripError, StripErrorCode
from thb_input.strip.llm import OpenAICompatibleLLMClient


class RespondLLMClient(Protocol):
    def complete_structured(self, prompt: RespondPrompt) -> object: ...


class OpenAICompatibleRespondLLMClient:
    def __init__(self, settings: Settings) -> None:
        model = (
            settings.respond_model
            or settings.strategize_model
            or settings.extract_model
            or settings.strip_model
        )
        if not model:
            self.client = None
            return
        provider_settings = settings.model_copy(
            update={
                "strip_model": model,
                "strip_temperature": settings.respond_temperature,
                "strip_max_tokens": settings.respond_max_tokens,
                "strip_output_mode": settings.respond_output_mode,
                "llm_timeout": settings.respond_timeout,
            }
        )
        self.client = OpenAICompatibleLLMClient(provider_settings, schema_name="thb_respond_result")

    def complete_structured(self, prompt: RespondPrompt) -> object:
        if self.client is None:
            raise RespondError(
                RespondErrorCode.LLM_CONFIGURATION_ERROR,
                "THB_RESPOND_MODEL is not configured and no fallback model is available",
            )
        try:
            return self.client.complete_structured(prompt)
        except StripError as exc:
            mapping = {
                StripErrorCode.LLM_CALL_FAILED: RespondErrorCode.LLM_CALL_FAILED,
                StripErrorCode.LLM_TIMEOUT: RespondErrorCode.LLM_TIMEOUT,
                StripErrorCode.LLM_CONFIGURATION_ERROR: RespondErrorCode.LLM_CONFIGURATION_ERROR,
                StripErrorCode.INVALID_STRUCTURED_OUTPUT: (
                    RespondErrorCode.INVALID_STRUCTURED_OUTPUT
                ),
            }
            raise RespondError(
                mapping.get(exc.code, RespondErrorCode.LLM_CALL_FAILED), exc.message
            ) from exc
