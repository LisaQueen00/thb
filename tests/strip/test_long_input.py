from thb_input.schemas.input import TextInputRequest
from thb_input.services.text_input import build_text_input_record
from thb_input.strip.service import StripService


class LongInputLLMClient:
    def __init__(self, source: str) -> None:
        self.source = source

    def complete_structured(self, prompt: object) -> object:
        return {"segments": [{"text": self.source, "labels": ["statement"]}]}


def test_long_repetitive_unicode_input_is_preserved_and_validated() -> None:
    source = "\n".join(f"第 {index:02d} 条消息：请确认✅！" for index in range(1, 31))
    canonical_input = build_text_input_record(TextInputRequest(source_message=source))

    result = StripService(LongInputLLMClient(source)).process(canonical_input)

    assert result.segments[0].text == source
    assert canonical_input.source_message == source

