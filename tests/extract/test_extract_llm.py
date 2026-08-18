import pytest
from tests.extract.helpers import make_request

from thb_input.config import Settings
from thb_input.extract.errors import ExtractError, ExtractErrorCode
from thb_input.extract.input_adapter import adapt_input
from thb_input.extract.llm import OpenAICompatibleExtractLLMClient
from thb_input.extract.prompt import build_extract_prompt


def test_extract_client_reuses_provider_with_independent_model_settings() -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key="test-key",
        strip_model="strip-model",
        extract_model="reasoning-model",
        extract_temperature=0.2,
        extract_max_tokens=7000,
        extract_output_mode="json_object",
        extract_timeout=90,
    )
    client = OpenAICompatibleExtractLLMClient(settings)

    assert client.client is not None
    assert client.client.settings.strip_model == "reasoning-model"
    assert client.client.settings.strip_temperature == 0.2
    assert client.client.settings.strip_max_tokens == 7000
    assert client.client.settings.llm_timeout == 90
    assert client.client.schema_name == "thb_extract_result"


def test_extract_client_requires_extract_model() -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key="test-key",
        strip_model=None,
        extract_model=None,
    )
    client = OpenAICompatibleExtractLLMClient(settings)
    request = make_request()
    prompt = build_extract_prompt(
        adapt_input(request.canonical_input, request.strip_result)
    )

    with pytest.raises(ExtractError) as caught:
        client.complete_structured(prompt)
    assert caught.value.code is ExtractErrorCode.LLM_CONFIGURATION_ERROR


def test_extract_client_can_fall_back_to_strip_model() -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key="test-key",
        strip_model="shared-model",
        extract_model=None,
    )
    client = OpenAICompatibleExtractLLMClient(settings)
    assert client.client is not None
    assert client.client.settings.strip_model == "shared-model"
