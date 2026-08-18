import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from thb_input.config import get_settings
from thb_input.respond.llm import OpenAICompatibleRespondLLMClient
from thb_input.respond.schemas import RespondRequest
from thb_input.respond.service import RespondService


def case(
    name: str,
    original_text: str,
    summary: str,
    strategy_type: str,
    goal: str,
    must_include: list[str],
    must_not_include: list[str],
    tone: str,
    boundary_level: str,
    commitment_level: str,
    what_not_to_accept: list[str] | None = None,
) -> tuple[str, str, RespondRequest]:
    request = RespondRequest.model_validate(
        {
            "selected_strategy": {
                "option_id": "strategy_001",
                "strategy_type": strategy_type,
                "title": goal,
                "goal": goal,
                "key_actions": must_include,
                "what_to_accept": [],
                "what_not_to_accept": what_not_to_accept or [],
                "clarification_needed": [],
                "benefits": ["推进当前事项并保持清晰沟通"],
                "tradeoffs": ["回复仅处理当前事项"],
                "risks": [],
                "prerequisites": [],
                "reply_constraints": {
                    "must_include": must_include,
                    "must_not_include": must_not_include,
                    "tone": tone,
                    "boundary_level": boundary_level,
                    "commitment_level": commitment_level,
                },
            },
            "relevant_event_context": {
                "event_summary": summary,
                "relevant_participants": ["用户", "对方"],
                "relevant_requests": [],
                "relevant_time_constraints": [],
            },
        }
    )
    return name, original_text, request


def main() -> None:
    cases = [
        case(
            "语气友好",
            "方便的话，能不能今天帮我确认一下文件？不着急，有结果告诉我就好，谢谢。",
            "对方礼貌询问用户能否今天确认文件，没有冲突或明显风险。",
            "progress",
            "自然回应并推进文件确认",
            ["今天确认文件情况"],
            [],
            "warm",
            "low",
            "limited",
        ),
        case(
            "无边界感",
            "你今晚必须把这个做完，别跟我说有什么困难，反正我明早必须看到结果。",
            "对方单方面要求今晚完成；用户尚未确认能够按该时间完成。",
            "boundary",
            "说明能力边界并给出可执行的确认安排",
            ["今晚无法确认完成", "明早确认后回复"],
            ["承认今晚是已约定期限", "保证今晚完成"],
            "firm",
            "medium",
            "limited",
            ["对方可以单方面决定用户的完成时间"],
        ),
        case(
            "肆意发泄",
            "你到底会不会做事？每次都拖拖拉拉，真是让人恶心。你这种人根本不靠谱，赶紧把项目进度发给我！",
            "对方使用多个人格攻击和情绪化表达，同时提出查看项目进度的事务性要求。",
            "boundary",
            "回应事务要求，同时明确沟通边界",
            ["项目进度会继续同步", "不接受针对个人的评价"],
            ["回击对方", "评价对方人格", "承担延误责任"],
            "firm",
            "high",
            "limited",
            ["对方对用户人格的负面评价"],
        ),
    ]
    settings = get_settings()

    def run(item: tuple[str, str, RespondRequest]) -> dict[str, object]:
        name, original_text, request = item
        service = RespondService(
            OpenAICompatibleRespondLLMClient(settings),
            validation_retries=settings.respond_validation_retries,
        )
        output = service.process(request)
        return {
            "case": name,
            "original_text": original_text,
            "respond_input": request.model_dump(mode="json"),
            "respond_output": output.model_dump(mode="json"),
        }

    outputs = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run, item) for item in cases]
        for future in as_completed(futures):
            outputs.append(future.result())
    order = {item[0]: index for index, item in enumerate(cases)}
    outputs.sort(key=lambda item: order[str(item["case"])])
    print(json.dumps(outputs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
