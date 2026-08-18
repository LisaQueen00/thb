from tests.extract.helpers import FakeLLM, empty_result, make_request

from thb_input.extract.service import ExtractService


def _relationship_payload(target: str) -> dict[str, object]:
    payload = empty_result()
    payload["participants"] = [
        {
            "participant_id": "participant_001",
            "name": "用户",
            "role": None,
            "source": "other",
            "epistemic_status": "reported_by_other",
            "supporting_segments": ["seg_001"],
        }
    ]
    payload["claims"] = [
        {
            "claim_id": "claim_001",
            "content": "对方主张文件已发送。",
            "source": "other",
            "epistemic_status": "reported_by_other",
            "supporting_segments": ["seg_001"],
        }
    ]
    payload["event_relationships"] = [
        {
            "relationship_id": "relationship_001",
            "type": "dependency_relation",
            "from_reference": "claim_001",
            "to_reference": target,
            "description": "确认请求指向用户。",
            "epistemic_status": "inferred",
            "supporting_segments": ["seg_001"],
        }
    ]
    return payload


def test_relationship_can_reference_participant() -> None:
    result = ExtractService(FakeLLM(_relationship_payload("participant_001"))).process(
        make_request()
    )
    assert result.event_relationships[0].to_reference == "participant_001"


def test_relationship_can_use_source_grounded_event_reference() -> None:
    result = ExtractService(FakeLLM(_relationship_payload("用户确认文件"))).process(
        make_request()
    )
    assert result.event_relationships[0].to_reference == "用户确认文件"
