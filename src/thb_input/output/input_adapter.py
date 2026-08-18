from dataclasses import dataclass

from thb_input.extract.schemas import ExtractResult
from thb_input.output.errors import OutputError, OutputErrorCode
from thb_input.output.schemas import OutputRequest
from thb_input.respond.schemas import RespondResult
from thb_input.strategize.schemas import StrategyOption


@dataclass(frozen=True)
class OutputModelInput:
    extract_result: ExtractResult
    selected_strategy: StrategyOption
    respond_result: RespondResult


def adapt_input(request: OutputRequest) -> OutputModelInput:
    if request.respond_result.strategy_option_id != request.selected_strategy.option_id:
        raise OutputError(
            OutputErrorCode.INPUT_CONTRACT_MISMATCH,
            "Respond strategy_option_id does not match selected_strategy.option_id",
        )
    constraints = request.selected_strategy.reply_constraints
    applied = request.respond_result.applied_constraints
    if (
        applied.tone is not constraints.tone
        or applied.boundary_level is not constraints.boundary_level
        or applied.commitment_level is not constraints.commitment_level
    ):
        raise OutputError(
            OutputErrorCode.INPUT_CONTRACT_MISMATCH,
            "Respond applied_constraints do not match the selected strategy",
        )
    return OutputModelInput(
        extract_result=request.extract_result,
        selected_strategy=request.selected_strategy,
        respond_result=request.respond_result,
    )
