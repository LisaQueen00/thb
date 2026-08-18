from thb_input.extract.schemas import ExtractRequest
from thb_input.schemas.input import TextInputRequest
from thb_input.services.text_input import build_text_input_record
from thb_input.strip.schemas import StripResult, StripSegment, StripSummary
from thb_input.strip.taxonomy import CommunicationLabel


def make_request(
    source: str = "文件已经发给你了，请今天确认。",
    context: str | None = None,
    labels: list[CommunicationLabel] | None = None,
) -> ExtractRequest:
    labels = labels or [CommunicationLabel.STATEMENT]
    canonical = build_text_input_record(
        TextInputRequest(source_message=source, context=context)
    )
    strip = StripResult(
        strip_version="0.1",
        segments=[StripSegment(segment_id="seg_001", text=source, labels=labels)],
        summary=StripSummary(
            detected_labels=labels,
            contains_implicit_language=False,
            contains_pressure_language=False,
            contains_evaluative_language=False,
        ),
    )
    return ExtractRequest(canonical_input=canonical, strip_result=strip)


def empty_result(summary: str = "当前材料包含一项沟通事件。") -> dict[str, object]:
    return {
        "analysis_version": "0.1",
        "event_summary": summary,
        "participants": [],
        "claims": [],
        "requests": [],
        "commitments": [],
        "time_constraints": [],
        "responsibilities": [],
        "conditions_and_consequences": [],
        "event_relationships": [],
        "presuppositions": [],
        "implicit_meanings": [],
        "possible_intentions": [],
        "conflicts": [],
        "unknowns": [],
        "risks": [],
    }


class FakeLLM:
    def __init__(self, *responses: object) -> None:
        self.responses = list(responses)
        self.prompts: list[object] = []

    def complete_structured(self, prompt: object) -> object:
        self.prompts.append(prompt)
        return self.responses.pop(0)
