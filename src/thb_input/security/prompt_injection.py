import re
from dataclasses import dataclass

_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "instruction_override",
        re.compile(
            r"忽略.{0,12}(之前|以上|先前).{0,12}(要求|指令|提示)|"
            r"ignore.{0,24}(previous|prior|above).{0,24}(instructions?|prompts?)",
            re.IGNORECASE,
        ),
    ),
    (
        "system_prompt_exfiltration",
        re.compile(
            r"(输出|显示|泄露|告诉.{0,8})(系统提示词|系统指令)|"
            r"(系统提示词|系统指令).{0,12}(输出|显示|泄露|告诉)|"
            r"(reveal|show|print|leak).{0,24}(system prompt|system instructions?)",
            re.IGNORECASE,
        ),
    ),
    (
        "role_override",
        re.compile(
            r"你现在(必须|是|扮演)|切换.{0,8}角色|"
            r"you are now|act as|switch.{0,12}role",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class PromptInjectionAssessment:
    detected: bool
    matched_rules: tuple[str, ...]


def detect_prompt_injection(value: str | None) -> PromptInjectionAssessment:
    """Flag injection-like patterns without deleting or rewriting input content."""
    if value is None:
        return PromptInjectionAssessment(detected=False, matched_rules=())

    matched_rules = tuple(rule for rule, pattern in _RULES if pattern.search(value))
    return PromptInjectionAssessment(
        detected=bool(matched_rules),
        matched_rules=matched_rules,
    )
