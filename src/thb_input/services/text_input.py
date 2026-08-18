from thb_input.schemas.input import (
    CaptureMethod,
    InputHandling,
    InputRecord,
    InputWarning,
    Platform,
    SourceMetadata,
    SourceType,
    TextInputRequest,
)
from thb_input.security.prompt_injection import detect_prompt_injection


def build_text_input_record(payload: TextInputRequest) -> InputRecord:
    """Build a deterministic record without interpreting or rewriting user content."""
    message_assessment = detect_prompt_injection(payload.source_message)
    context_assessment = detect_prompt_injection(payload.context)
    detected_fields = [
        field
        for field, detected in (
            ("source_message", message_assessment.detected),
            ("context", context_assessment.detected),
        )
        if detected
    ]
    matched_rules = list(
        dict.fromkeys(
            (*message_assessment.matched_rules, *context_assessment.matched_rules)
        )
    )
    injection_detected = bool(detected_fields)

    return InputRecord(
        source_message=payload.source_message,
        context=payload.context,
        source_metadata=SourceMetadata(
            source_type=SourceType.PASTED_TEXT,
            capture_method=CaptureMethod.PASTE,
            platform=Platform.UNKNOWN,
            participants=[],
            timestamp=None,
            message_order_preserved=True,
        ),
        raw_source=None,
        unknown_fields=[
            "source_metadata.platform",
            "source_metadata.participants",
            "source_metadata.timestamp",
            "raw_source",
        ],
        warnings=(
            [
                InputWarning(
                    code="prompt_injection_detected",
                    fields=detected_fields,
                    rules=matched_rules,
                )
            ]
            if injection_detected
            else []
        ),
        input_handling=InputHandling(
            prompt_injection_detected=injection_detected,
            handling=(
                "detected_but_preserved_as_data"
                if injection_detected
                else "preserved_as_untrusted_data"
            ),
            detected_fields=detected_fields,
            matched_rules=matched_rules,
        ),
    )
