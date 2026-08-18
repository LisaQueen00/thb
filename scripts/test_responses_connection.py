import argparse

import httpx

from thb_input.config import Settings

parser = argparse.ArgumentParser(description="Test a Responses-compatible provider.")
parser.add_argument("--env-file", default=".env")
args = parser.parse_args()

settings = Settings(_env_file=args.env_file)
if not settings.llm_api_key or not settings.strip_model:
    raise RuntimeError("LLM API key and model must be configured")

url = f"{settings.llm_base_url.rstrip('/')}/responses"
response = httpx.post(
    url,
    headers={"Authorization": f"Bearer {settings.llm_api_key}"},
    json={"model": settings.strip_model, "input": "Reply with exactly: CONNECTED"},
    timeout=settings.llm_timeout,
)
if response.is_error:
    try:
        error_body = response.json()
        error = error_body.get("error", {})
        print(f"HTTP_STATUS: {response.status_code}")
        print(f"ERROR_CODE: {error.get('code', 'unknown')}")
        print(f"ERROR_MESSAGE: {error.get('message', 'provider request failed')}")
    except ValueError:
        print(f"HTTP_STATUS: {response.status_code}")
        print("ERROR_CODE: non_json_provider_error")
    raise SystemExit(1)
envelope = response.json()

output_text = envelope.get("output_text")
if output_text is None:
    parts = []
    for item in envelope.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                parts.append(content.get("text", ""))
    output_text = "".join(parts)

print(f"HTTP_STATUS: {response.status_code}")
print(f"RESPONSE_STATUS: {envelope.get('status', 'unknown')}")
print(f"OUTPUT_TEXT_PRESENT: {bool(output_text)}")
print(f"OUTPUT_TEXT: {output_text}")
