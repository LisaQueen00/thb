from thb_input.extract.schemas import EpistemicStatus, EvidenceSource


def source_statement(
    content: str,
    source: EvidenceSource,
    status: EpistemicStatus | None = None,
) -> str:
    if status is EpistemicStatus.INFERRED:
        return f"目前只能推测：{content}"
    if status is EpistemicStatus.UNKNOWN:
        return f"目前无法确认：{content}"
    if status is EpistemicStatus.CONFLICTING:
        return f"关于“{content}”，双方说法不一致"
    if source is EvidenceSource.OTHER or status is EpistemicStatus.REPORTED_BY_OTHER:
        if content.startswith(("对方", "另一方")):
            return content
        return f"对方表示：{content}"
    if source is EvidenceSource.USER_CONTEXT or status is EpistemicStatus.REPORTED_BY_USER:
        return f"你提供的背景是：{content}"
    if source is EvidenceSource.BOTH or status is EpistemicStatus.SUPPORTED_BY_BOTH:
        return f"双方信息均支持：{content}"
    return content


def actor_label(actor: str) -> str:
    normalized = actor.strip().lower()
    if normalized in {"other", "counterparty", "对方"}:
        return "对方"
    if normalized in {"user", "用户", "我"}:
        return "你"
    return actor
