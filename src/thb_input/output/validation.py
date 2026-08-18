from thb_input.output.composers import compose_output
from thb_input.output.errors import OutputError, OutputErrorCode
from thb_input.output.input_adapter import OutputModelInput
from thb_input.output.schemas import OutputResult


def validate_output(result: OutputResult, model_input: OutputModelInput) -> OutputResult:
    if result.reply.content != model_input.respond_result.reply:
        raise _invalid("Output reply must preserve RespondResult.reply exactly")
    if result.strategy.strategy_option_id != model_input.selected_strategy.option_id:
        raise _invalid("Output strategy ID must preserve the selected strategy ID")
    if result.strategy.strategy_option_id != model_input.respond_result.strategy_option_id:
        raise _invalid("Output strategy ID must match RespondResult.strategy_option_id")

    expected = compose_output(model_input)
    if result != expected:
        raise _invalid(
            "Output contains content that is not produced by the deterministic composers"
        )
    return result


def _invalid(message: str) -> OutputError:
    return OutputError(OutputErrorCode.OUTPUT_VALIDATION_FAILED, message)
