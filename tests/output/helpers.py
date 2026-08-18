from tests.extract.helpers import empty_result
from tests.strategize.helpers import option

from thb_input.extract.schemas import ExtractResult
from thb_input.output.schemas import OutputRequest
from thb_input.respond.schemas import RespondResult
from thb_input.strategize.schemas import StrategyOption


def make_output_request(
    *,
    extract_updates: dict[str, object] | None = None,
    strategy_updates: dict[str, object] | None = None,
    respond_updates: dict[str, object] | None = None,
) -> OutputRequest:
    extract_payload = empty_result("对方希望用户确认文件。")
    extract_payload.update(extract_updates or {})
    strategy_payload = option("strategy_001", "progress")
    strategy_payload.update(strategy_updates or {})
    strategy = StrategyOption.model_validate(strategy_payload)
    respond_payload: dict[str, object] = {
        "respond_version": "0.1",
        "strategy_option_id": "strategy_001",
        "reply": "文件情况我确认后回复你。",
        "applied_constraints": {
            "tone": strategy.reply_constraints.tone,
            "boundary_level": strategy.reply_constraints.boundary_level,
            "commitment_level": strategy.reply_constraints.commitment_level,
        },
    }
    respond_payload.update(respond_updates or {})
    return OutputRequest(
        extract_result=ExtractResult.model_validate(extract_payload),
        selected_strategy=strategy,
        respond_result=RespondResult.model_validate(respond_payload),
    )
