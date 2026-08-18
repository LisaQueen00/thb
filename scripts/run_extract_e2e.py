"""Run one real Input -> Strip -> Extract acceptance case."""

import json

from thb_input.api.v1.extract import get_extract_service
from thb_input.api.v1.strip import get_strip_service
from thb_input.extract.schemas import ExtractRequest
from thb_input.schemas.input import TextInputRequest
from thb_input.services.text_input import build_text_input_record


def main() -> None:
    canonical = build_text_input_record(
        TextInputRequest(
            source_message="文件已经发给你了，请今天确认。",
            context=None,
        )
    )
    strip_result = get_strip_service().process(canonical)
    extract_result = get_extract_service().process(
        ExtractRequest(canonical_input=canonical, strip_result=strip_result)
    )
    print(
        json.dumps(
            {
                "analysis_version": extract_result.analysis_version,
                "event_summary": extract_result.event_summary,
                "claims": len(extract_result.claims),
                "requests": len(extract_result.requests),
                "time_constraints": len(extract_result.time_constraints),
                "risks": [
                    {
                        "type": risk.risk_type,
                        "description": risk.description,
                        "confidence": risk.confidence,
                    }
                    for risk in extract_result.risks
                ],
                "evidence_ids": sorted(
                    {
                        segment_id
                        for claim in extract_result.claims
                        for segment_id in claim.supporting_segments
                    }
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
