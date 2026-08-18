from dataclasses import dataclass

from thb_input.extract.schemas import ExtractResult
from thb_input.strategize.schemas import StrategyType


@dataclass(frozen=True)
class StrategizeAcceptanceCase:
    name: str
    extract_result: ExtractResult
    explicit_goal: str | None
    required_types: frozenset[StrategyType]
    forbidden_types: frozenset[StrategyType] = frozenset()
    requires_user_input: bool = False


def _event(summary: str, **updates: object) -> ExtractResult:
    payload: dict[str, object] = {
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
    payload.update(updates)
    return ExtractResult.model_validate(payload)


def _request(action: str, strength: str = "request") -> dict[str, object]:
    return {
        "request_id": "req_001",
        "actor": "other",
        "target": "user",
        "action": action,
        "requested_time": None,
        "strength": strength,
        "source": "other",
        "supporting_segments": ["seg_001"],
    }


def _risk(risk_type: str, description: str) -> dict[str, object]:
    return {
        "risk_id": "risk_001",
        "risk_type": risk_type,
        "description": description,
        "confidence": "high",
        "basis": description,
        "supporting_segments": ["seg_001"],
    }


def _unknown(description: str) -> dict[str, object]:
    return {
        "unknown_id": "unknown_001",
        "description": description,
        "importance": "high",
        "reason": "该信息会直接影响策略或承诺。",
    }


def _deadline_conflict() -> dict[str, object]:
    return {
        "conflict_id": "conflict_001",
        "topic": "交付期限",
        "positions": [
            {
                "source": "other",
                "content": "对方主张期限是今天。",
                "supporting_segments": ["seg_001"],
            },
            {
                "source": "user_context",
                "content": "用户称双方确认的是周一。",
                "supporting_segments": [],
            },
        ],
        "resolution": "unresolved",
    }


ACCEPTANCE_CASES = (
    StrategizeAcceptanceCase(
        "01_ordinary_transaction",
        _event(
            "对方礼貌请求用户今天确认文件，没有明显冲突或风险。",
            requests=[_request("确认文件")],
        ),
        None,
        frozenset({StrategyType.PROGRESS}),
        frozenset({StrategyType.BOUNDARY, StrategyType.DECLINE}),
    ),
    StrategizeAcceptanceCase(
        "02_deadline_conflict",
        _event(
            "对方主张期限是今天，用户称期限为周一，冲突未解决。",
            conflicts=[_deadline_conflict()],
        ),
        None,
        frozenset({StrategyType.CLARIFY, StrategyType.PROGRESS}),
    ),
    StrategizeAcceptanceCase(
        "03_aggressive_with_valid_task",
        _event(
            "对方使用攻击性评价，同时提出了需要用户完成材料的合理工作要求。",
            requests=[_request("完成材料", "demand")],
        ),
        None,
        frozenset({StrategyType.PROGRESS, StrategyType.BOUNDARY}),
        frozenset({StrategyType.DECLINE}),
    ),
    StrategizeAcceptanceCase(
        "04_responsibility_risk",
        _event(
            "对方要求今天完成，并声称未来全部问题由用户负责。",
            requests=[_request("今天完成", "demand")],
            risks=[_risk("responsibility_risk", "对方试图将全部后续责任归于用户。")],
        ),
        None,
        frozenset({StrategyType.RISK_REDUCTION}),
    ),
    StrategizeAcceptanceCase(
        "05_irreversible_action",
        _event(
            "对方要求用户先签署，但关键细节未知，存在不可逆行动风险。",
            requests=[_request("先签署文件", "demand")],
            unknowns=[_unknown("待签署文件的关键条款和责任范围未知。")],
            risks=[_risk("irreversible_action_risk", "签署可能形成不可逆承诺。")],
        ),
        None,
        frozenset({StrategyType.RISK_REDUCTION, StrategyType.CLARIFY}),
    ),
    StrategizeAcceptanceCase(
        "06_explicit_decline_keep_relationship",
        _event(
            "对方请求用户提供帮助，用户可以接受或拒绝该请求。",
            requests=[_request("提供额外帮助")],
        ),
        "不答应要求，同时尽量维持关系",
        frozenset({StrategyType.DECLINE, StrategyType.BOUNDARY}),
    ),
    StrategizeAcceptanceCase(
        "07_goal_conflicts_with_risk",
        _event(
            "用户希望尽快结束事项，但关键条件未知且存在高承诺风险。",
            requests=[_request("立即确认全部条件", "demand")],
            unknowns=[_unknown("承诺所包含的关键条件未知。")],
            risks=[_risk("commitment_risk", "立即确认可能形成范围不明的承诺。")],
        ),
        "尽快结束这件事",
        frozenset({StrategyType.RISK_REDUCTION}),
    ),
    StrategizeAcceptanceCase(
        "08_missing_completion_time",
        _event(
            "对方要求用户提供完成时间，但用户真实可完成时间未知。",
            requests=[_request("说明完成时间")],
            unknowns=[_unknown("用户真实可完成时间未知。")],
        ),
        None,
        frozenset({StrategyType.CLARIFY}),
        requires_user_input=True,
    ),
    StrategizeAcceptanceCase(
        "09_healthy_communication",
        _event(
            "对方友好请求三点前提供资料；如果来不及，可以说明预计时间。",
            requests=[_request("提供资料或说明预计时间")],
        ),
        None,
        frozenset({StrategyType.PROGRESS}),
        frozenset({StrategyType.BOUNDARY, StrategyType.RISK_REDUCTION}),
    ),
    StrategizeAcceptanceCase(
        "10_complex_conflict",
        _event(
            "存在期限冲突、群体压力、人格评价、责任风险和真实业务依赖。",
            requests=[_request("推进业务事项", "demand")],
            conflicts=[_deadline_conflict()],
            risks=[_risk("responsibility_risk", "存在扩大用户责任的风险。")],
        ),
        "保证推进，同时保护责任边界",
        frozenset({StrategyType.PROGRESS, StrategyType.RISK_REDUCTION}),
    ),
)
