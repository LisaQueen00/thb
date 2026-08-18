import pytest
from tests.strategize.helpers import make_request

from thb_input.config import Settings
from thb_input.strategize.errors import StrategizeError, StrategizeErrorCode
from thb_input.strategize.input_adapter import adapt_input
from thb_input.strategize.llm import OpenAICompatibleStrategizeLLMClient
from thb_input.strategize.prompt import build_strategize_prompt


def test_client_uses_independent_strategize_configuration() -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key="test-key",
        strip_model="strip-model",
        extract_model="extract-model",
        strategize_model="strategy-model",
        strategize_temperature=0.1,
        strategize_max_tokens=7000,
        strategize_output_mode="json_object",
        strategize_timeout=90,
    )
    client = OpenAICompatibleStrategizeLLMClient(settings)
    assert client.client is not None
    assert client.client.settings.strip_model == "strategy-model"
    assert client.client.settings.strip_temperature == 0.1
    assert client.client.settings.strip_max_tokens == 7000
    assert client.client.settings.llm_timeout == 90
    assert client.client.schema_name == "thb_strategize_result"


def test_client_falls_back_to_extract_model() -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key="test-key",
        extract_model="extract-model",
        strategize_model=None,
    )
    client = OpenAICompatibleStrategizeLLMClient(settings)
    assert client.client is not None
    assert client.client.settings.strip_model == "extract-model"


def test_client_requires_any_configured_model() -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key="test-key",
        strip_model=None,
        extract_model=None,
        strategize_model=None,
    )
    client = OpenAICompatibleStrategizeLLMClient(settings)
    prompt = build_strategize_prompt(adapt_input(make_request()))
    with pytest.raises(StrategizeError) as caught:
        client.complete_structured(prompt)
    assert caught.value.code is StrategizeErrorCode.LLM_CONFIGURATION_ERROR
