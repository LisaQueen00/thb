import logging

from thb_input.output.composers import compose_output
from thb_input.output.input_adapter import adapt_input
from thb_input.output.schemas import OutputRequest, OutputResult
from thb_input.output.validation import validate_output

logger = logging.getLogger(__name__)


class OutputService:
    def process(self, request: OutputRequest) -> OutputResult:
        model_input = adapt_input(request)
        result = compose_output(model_input)
        validate_output(result, model_input)
        logger.info(
            "output_completed strategy_option_id=%s attention_items=%d",
            result.strategy.strategy_option_id,
            len(result.attention),
        )
        return result
