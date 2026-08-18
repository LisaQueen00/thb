"""Run a real Input -> Strip HTTP acceptance check against the configured model."""

import json

from fastapi.testclient import TestClient

from thb_input.main import app


def main() -> None:
    source_message = "大家都等着你，你今天必须处理。"
    context = "对方在项目群里催促我。"
    client = TestClient(app)

    input_response = client.post(
        "/api/v1/input/text",
        json={"source_message": source_message, "context": context},
    )
    input_response.raise_for_status()
    canonical_input = input_response.json()

    strip_response = client.post("/api/v1/strip", json=canonical_input)
    strip_response.raise_for_status()
    strip_result = strip_response.json()

    reconstructed = "".join(segment["text"] for segment in strip_result["segments"])
    if reconstructed != source_message:
        raise RuntimeError("Strip segments do not preserve the source message exactly")
    if canonical_input["source_message"] != source_message:
        raise RuntimeError("Input canonical object changed the source message")
    if canonical_input["context"] != context:
        raise RuntimeError("Input canonical object changed the context")

    print(
        json.dumps(
            {
                "input_status": input_response.status_code,
                "strip_status": strip_response.status_code,
                "source_preserved": True,
                "context_preserved": True,
                "segment_count": len(strip_result["segments"]),
                "labels": sorted(
                    {
                        label
                        for segment in strip_result["segments"]
                        for label in segment["labels"]
                    }
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
