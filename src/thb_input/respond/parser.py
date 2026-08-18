import json
from collections.abc import Mapping

from thb_input.respond.errors import RespondError, RespondErrorCode


def parse_model_response(raw_response: object) -> dict[str, object]:
    if isinstance(raw_response, Mapping):
        return dict(raw_response)
    if not isinstance(raw_response, str):
        raise _invalid("Model response must be a JSON object or JSON string")
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise _invalid("Model response is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise _invalid("Model response JSON root must be an object")
    return parsed


def _invalid(message: str) -> RespondError:
    return RespondError(RespondErrorCode.INVALID_STRUCTURED_OUTPUT, message)
