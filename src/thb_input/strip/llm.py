import json
from collections.abc import Mapping
from typing import Protocol

import httpx

from thb_input.config import Settings
from thb_input.strip.errors import StripError, StripErrorCode
from thb_input.strip.prompt import StripPrompt


class LLMClient(Protocol):
    def complete_structured(self, prompt: StripPrompt) -> object: ...


class OpenAICompatibleLLMClient:
    """Minimal provider boundary for OpenAI-compatible chat completion APIs."""

    def __init__(self, settings: Settings, http_client: httpx.Client | None = None) -> None:
        self.settings = settings
        self.http_client = http_client

    def complete_structured(self, prompt: StripPrompt) -> object:
        if not self.settings.llm_api_key:
            raise StripError(
                StripErrorCode.LLM_CONFIGURATION_ERROR,
                "THB_LLM_API_KEY is not configured",
            )
        if not self.settings.strip_model:
            raise StripError(
                StripErrorCode.LLM_CONFIGURATION_ERROR,
                "THB_STRIP_MODEL is not configured",
            )

        system_content = prompt.system
        if self.settings.strip_output_mode == "json_object":
            system_content = (
                f"{system_content}\n\nREQUIRED JSON SCHEMA\n"
                f"{json.dumps(prompt.output_schema, ensure_ascii=False)}"
            )

        if self.settings.llm_api_style == "responses":
            payload = self._build_responses_payload(prompt, system_content)
            url = f"{self.settings.llm_base_url.rstrip('/')}/responses"
        else:
            payload = self._build_chat_payload(prompt, system_content)
            url = f"{self.settings.llm_base_url.rstrip('/')}/chat/completions"

        for attempt in range(self.settings.llm_max_retries + 1):
            try:
                response = self._post(url, payload)
                response.raise_for_status()
                envelope = response.json()
                if self.settings.llm_api_style == "responses":
                    return self._extract_responses_content(envelope)
                return self._extract_chat_content(envelope)
            except httpx.TimeoutException as exc:
                if attempt >= self.settings.llm_max_retries:
                    raise StripError(StripErrorCode.LLM_TIMEOUT, "LLM request timed out") from exc
            except (httpx.NetworkError, httpx.RemoteProtocolError) as exc:
                if attempt >= self.settings.llm_max_retries:
                    raise StripError(
                        StripErrorCode.LLM_CALL_FAILED,
                        "LLM network request failed",
                    ) from exc
            except httpx.HTTPStatusError as exc:
                retryable = exc.response.status_code == 429 or exc.response.status_code >= 500
                if not retryable or attempt >= self.settings.llm_max_retries:
                    raise StripError(
                        StripErrorCode.LLM_CALL_FAILED,
                        f"LLM provider returned HTTP {exc.response.status_code}",
                    ) from exc
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise StripError(
                    StripErrorCode.INVALID_STRUCTURED_OUTPUT,
                    f"LLM provider response envelope is invalid: {exc}",
                ) from exc

        raise StripError(StripErrorCode.LLM_CALL_FAILED, "LLM request failed")

    def _build_chat_payload(
        self, prompt: StripPrompt, system_content: str
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "model": self.settings.strip_model,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt.user},
            ],
            "temperature": self.settings.strip_temperature,
            "max_tokens": self.settings.strip_max_tokens,
        }
        if self.settings.strip_output_mode == "json_schema":
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "thb_strip_result",
                    "strict": True,
                    "schema": prompt.output_schema,
                },
            }
        else:
            payload["response_format"] = {"type": "json_object"}
        return payload

    def _build_responses_payload(
        self, prompt: StripPrompt, system_content: str
    ) -> dict[str, object]:
        if self.settings.strip_output_mode == "json_schema":
            output_format: dict[str, object] = {
                "type": "json_schema",
                "name": "thb_strip_result",
                "strict": True,
                "schema": prompt.output_schema,
            }
        else:
            output_format = {"type": "json_object"}
        return {
            "model": self.settings.strip_model,
            "instructions": system_content,
            "input": prompt.user,
            "max_output_tokens": self.settings.strip_max_tokens,
            "text": {"format": output_format},
        }

    def _post(self, url: str, payload: dict[str, object]) -> httpx.Response:
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        if self.http_client is not None:
            return self.http_client.post(url, headers=headers, json=payload)
        with httpx.Client(timeout=self.settings.llm_timeout) as client:
            return client.post(url, headers=headers, json=payload)

    @staticmethod
    def _extract_chat_content(envelope: object) -> object:
        if not isinstance(envelope, Mapping):
            raise TypeError("provider envelope must be an object")
        choices = envelope["choices"]
        choice = choices[0]
        message = choice["message"]
        if not isinstance(message, Mapping):
            raise TypeError("provider message must be an object")
        if message.get("parsed") is not None:
            return message["parsed"]
        if message.get("refusal"):
            raise ValueError("provider refused the structured-output request")
        content = message.get("content")
        if content is None:
            fields = ",".join(sorted(str(field) for field in message))
            raise ValueError(
                "provider message has no content "
                f"(finish_reason={choice.get('finish_reason')}, fields={fields})"
            )
        if isinstance(content, list):
            text_parts = [
                part["text"]
                for part in content
                if isinstance(part, Mapping) and part.get("type") == "text"
            ]
            return "".join(text_parts)
        return content

    @staticmethod
    def _extract_responses_content(envelope: object) -> object:
        if not isinstance(envelope, Mapping):
            raise TypeError("provider envelope must be an object")
        if envelope.get("output_text"):
            return envelope["output_text"]

        text_parts: list[str] = []
        for item in envelope.get("output", []):
            if not isinstance(item, Mapping):
                continue
            for content in item.get("content", []):
                if not isinstance(content, Mapping):
                    continue
                if content.get("type") == "refusal":
                    raise ValueError("provider refused the structured-output request")
                if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                    text_parts.append(content["text"])
        if text_parts:
            return "".join(text_parts)
        raise ValueError(
            "provider Responses envelope has no output text "
            f"(status={envelope.get('status')})"
        )
