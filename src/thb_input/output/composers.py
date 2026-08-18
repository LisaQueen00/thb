from thb_input.extract.schemas import (
    ConditionConsequenceKind,
    ConflictPosition,
    EvidenceSource,
    ExtractResult,
    RequestStrength,
    TimeConstraintType,
)
from thb_input.output.input_adapter import OutputModelInput
from thb_input.output.schemas import (
    CounterpartyRequest,
    EventLogic,
    OutputResult,
    PlainLanguage,
    ReplyDisplay,
    StrategyDisplay,
)
from thb_input.output.templates import actor_label, source_statement
from thb_input.strategize.schemas import StrategyOption


def compose_counterparty_request(event: ExtractResult) -> CounterpartyRequest:
    counterparty_requests = [
        item
        for item in event.requests
        if actor_label(item.actor) == "对方" and actor_label(item.target) == "你"
    ]
    actions = [
        _request_action(item.action, item.strength, item.source)
        for item in counterparty_requests
    ]
    requested_time = []
    for item in counterparty_requests:
        if item.requested_time:
            text = f"对方希望时间为{item.requested_time}"
            if item.source is EvidenceSource.USER_CONTEXT:
                text = "根据你提供的背景，" + text
            requested_time.append(text)
    if not requested_time:
        for item in event.time_constraints:
            if item.source not in {EvidenceSource.OTHER, EvidenceSource.BOTH}:
                continue
            if item.type is TimeConstraintType.CLAIMED_AGREED_DEADLINE:
                requested_time.append(f"对方称此前约定时间为{item.expression}")
            elif item.type in {
                TimeConstraintType.REQUESTED_DEADLINE,
                TimeConstraintType.AMBIGUOUS_DEADLINE,
            }:
                requested_time.append(f"对方希望时间为{item.expression}")

    conditions = [
        source_statement(item.content, item.source, item.epistemic_status)
        for item in event.conditions_and_consequences
        if item.kind is ConditionConsequenceKind.CONDITION
        and item.source in {EvidenceSource.OTHER, EvidenceSource.BOTH}
    ]
    consequences = [
        source_statement(item.content, item.source, item.epistemic_status)
        for item in event.conditions_and_consequences
        if item.kind is not ConditionConsequenceKind.CONDITION
        and item.source in {EvidenceSource.OTHER, EvidenceSource.BOTH}
    ]
    return CounterpartyRequest(
        actions=_unique(actions)[:3],
        requested_time=_unique(requested_time)[:3],
        conditions=_unique(conditions)[:3],
        claimed_consequences=_unique(consequences)[:3],
    )


def compose_event_logic(event: ExtractResult) -> EventLogic:
    prior_markers = ("此前", "之前", "上周", "昨天", "曾经", "已经")
    current_state = []
    prior_events = []
    for claim in event.claims:
        rendered = source_statement(claim.content, claim.source, claim.epistemic_status)
        target = (
            prior_events
            if any(marker in claim.content for marker in prior_markers)
            else current_state
        )
        target.append(rendered)

    current_requests = [
        _event_request(item.actor, item.target, item.action, item.source)
        for item in event.requests
    ]
    time_logic = [
        _time_logic(item.expression, item.type, item.source)
        for item in event.time_constraints
    ]
    responsibility_logic = [
        source_statement(
            f"{actor_label(item.actor)}的责任被描述为：{item.content}",
            item.source,
            item.epistemic_status,
        )
        for item in event.responsibilities
    ]
    dependencies = [
        source_statement(item.description, EvidenceSource.BOTH, item.epistemic_status)
        for item in event.event_relationships
    ]
    conflicts = [_render_conflict(item.topic, item.positions) for item in event.conflicts]
    unknowns = [f"目前无法确认：{item.description}" for item in event.unknowns]
    sections = _limit_event_logic(
        {
            "current_state": _unique(current_state),
            "prior_events": _unique(prior_events),
            "current_requests": _unique(current_requests),
            "time_logic": _unique(time_logic),
            "responsibility_logic": _unique(responsibility_logic),
            "dependencies": _unique(dependencies),
            "conflicts": _unique(conflicts),
            "unknowns": _unique(unknowns),
        }
    )
    return EventLogic(**sections)


def select_attention(event: ExtractResult) -> list[str]:
    attention = [
        _render_conflict(item.topic, item.positions)
        for item in event.conflicts
        if item.resolution == "unresolved"
    ]
    attention.extend(
        f"目前无法确认：{item.description}"
        for item in event.unknowns
        if item.importance.value == "high"
    )
    attention.extend(
        f"需要注意：{item.description}"
        for item in event.risks
        if item.confidence.value == "high"
    )
    attention.extend(
        f"这段表达可能意味着：{item.content}"
        for item in event.implicit_meanings
        if item.confidence.value in {"high", "medium"}
    )
    return _unique(attention)[:3]


def compose_strategy(strategy: StrategyOption) -> StrategyDisplay:
    summary = strategy.goal
    if strategy.what_not_to_accept:
        summary += "；同时不要接受：" + "、".join(strategy.what_not_to_accept)
    return StrategyDisplay(
        strategy_option_id=strategy.option_id,
        title=strategy.title,
        summary=summary,
        key_actions=strategy.key_actions,
    )


def compose_output(model_input: OutputModelInput) -> OutputResult:
    event = model_input.extract_result
    strategy = model_input.selected_strategy
    response = model_input.respond_result
    return OutputResult(
        output_version="0.1",
        plain_language=PlainLanguage(content=event.event_summary),
        counterparty_request=compose_counterparty_request(event),
        event_logic=compose_event_logic(event),
        attention=select_attention(event),
        strategy=compose_strategy(strategy),
        reply=ReplyDisplay(content=response.reply, copyable=True),
    )


def _render_conflict(topic: str, positions: list[ConflictPosition]) -> str:
    rendered = [source_statement(item.content, item.source) for item in positions]
    return f"关于{topic}，双方说法不一致：" + "；".join(rendered)


def _request_action(
    action: str, strength: RequestStrength, source: EvidenceSource
) -> str:
    text = f"对方{'要求' if strength is RequestStrength.DEMAND else '希望'}你{action}"
    if source is EvidenceSource.USER_CONTEXT:
        return "根据你提供的背景，" + text
    return text


def _event_request(
    actor: str, target: str, action: str, source: EvidenceSource
) -> str:
    text = f"{actor_label(actor)}要求{actor_label(target)}{action}"
    if source is EvidenceSource.USER_CONTEXT:
        return "根据你提供的背景，" + text
    return text


def _time_logic(
    expression: str,
    kind: TimeConstraintType,
    source: EvidenceSource,
) -> str:
    if kind is TimeConstraintType.CLAIMED_AGREED_DEADLINE:
        return f"对方称此前约定时间是{expression}"
    if kind is TimeConstraintType.USER_REPORTED_DEADLINE:
        return f"你提供的背景时间是{expression}"
    if kind is TimeConstraintType.SUPPORTED_DEADLINE:
        return f"双方信息支持的时间是{expression}"
    if kind is TimeConstraintType.AMBIGUOUS_DEADLINE:
        return f"时间表达尚不明确：{expression}"
    if source is EvidenceSource.USER_CONTEXT:
        return f"根据你提供的背景，对方希望时间为{expression}"
    return f"对方当前要求的时间是{expression}"


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item.strip()))


def _limit_event_logic(sections: dict[str, list[str]]) -> dict[str, list[str]]:
    """Keep every populated category visible without turning Output into an Extract dump."""
    limited = {name: values[:1] for name, values in sections.items()}
    remaining = 14 - sum(len(values) for values in limited.values())
    priority = (
        "current_state",
        "current_requests",
        "time_logic",
        "conflicts",
        "unknowns",
        "responsibility_logic",
        "dependencies",
        "prior_events",
    )
    for index in (1, 2):
        for name in priority:
            if remaining <= 0:
                return limited
            values = sections[name]
            if len(values) > index:
                limited[name].append(values[index])
                remaining -= 1
    return limited
