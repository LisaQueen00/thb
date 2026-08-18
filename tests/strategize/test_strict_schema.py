from collections.abc import Mapping

from thb_input.strategize.schemas import StrategizeResult


def test_structured_output_schema_requires_every_declared_property() -> None:
    schema = StrategizeResult.model_json_schema()
    objects = [schema, *schema["$defs"].values()]
    for item in objects:
        if not isinstance(item, Mapping) or item.get("type") != "object":
            continue
        properties = item.get("properties", {})
        assert set(item.get("required", [])) == set(properties)
        assert item.get("additionalProperties") is False
