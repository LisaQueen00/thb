import json

import httpx
import pytest

from thb_input.config import Settings
from thb_input.strip.errors import StripError, StripErrorCode
from thb_input.strip.llm import OpenAICompatibleLLMClient
from thb_input.strip.prompt import StripPrompt

PROMPT = StripPrompt(system="system", user="user", output_schema={"type": "object"})


def test_client_requires_api_key() -> None:
    client = OpenAICompatibleLLMClient(
        Settings(_env_file=None, llm_api_key=None, strip_model="test-model")
    )

    with pytest.raises(StripError) as raised:
        client.complete_structured(PROMPT)

    assert raised.value.code is StripErrorCode.LLM_CONFIGURATION_ERROR


def test_client_retries_retryable_provider_error_and_returns_content() -> None:
    calls = 0
    result = {"strip_version": "0.1"}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.headers["authorization"] == "Bearer secret"
        payload = json.loads(request.content)
        assert payload["response_format"]["type"] == "json_schema"
        if calls == 1:
            return httpx.Response(500, request=request)
        return httpx.Response(
            200,
            request=request,
            json={"choices": [{"message": {"content": json.dumps(result)}}]},
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = Settings(
        _env_file=None,
        llm_api_key="secret",
        strip_model="test-model",
        llm_base_url="https://provider.test/v1",
        llm_max_retries=1,
        llm_api_style="chat_completions",
    )
    client = OpenAICompatibleLLMClient(settings, http_client)

    assert client.complete_structured(PROMPT) == json.dumps(result)
    assert calls == 2


def test_client_supports_responses_api_structured_output() -> None:
    result = {"strip_version": "0.1"}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/responses"
        payload = json.loads(request.content)
        assert payload["text"]["format"]["type"] == "json_schema"
        assert payload["instructions"] == "system"
        return httpx.Response(
            200,
            request=request,
            json={
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": json.dumps(result)}
                        ],
                    }
                ],
            },
        )

    settings = Settings(
        _env_file=None,
        llm_api_key="secret",
        strip_model="test-model",
        llm_base_url="https://provider.test/v1",
        llm_api_style="responses",
    )
    http_client = httpx.Client(transport=httpx.MockTransport(handler))

    assert OpenAICompatibleLLMClient(settings, http_client).complete_structured(
        PROMPT
    ) == json.dumps(result)
