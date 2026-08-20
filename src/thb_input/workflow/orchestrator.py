import time
from collections.abc import Callable
from typing import Protocol, TypeVar, cast

from thb_input.config import Settings, get_settings
from thb_input.extract.llm import OpenAICompatibleExtractLLMClient
from thb_input.extract.schemas import ExtractRequest, ExtractResult
from thb_input.extract.service import ExtractService
from thb_input.meaning import MeaningResult, MeaningService
from thb_input.schemas.input import InputRecord, TextInputRequest
from thb_input.services.text_input import build_text_input_record
from thb_input.strip.llm import OpenAICompatibleLLMClient
from thb_input.strip.schemas import StripResult
from thb_input.strip.service import StripService

from .errors import WorkflowError
from .state import THBState, WorkflowStage, WorkflowStatus

T = TypeVar("T")


class Processor(Protocol):
    def process(self, request: object) -> object: ...


class THBWorkflow:
    def __init__(
        self,
        config: Settings | None = None,
        *,
        input_service: Callable[[TextInputRequest], InputRecord] = build_text_input_record,
        strip_service: Processor | None = None,
        extract_service: Processor | None = None,
        meaning_service: Processor | None = None,
    ) -> None:
        settings = config or get_settings()
        self.input_service = input_service
        self.strip_service = strip_service or StripService(
            OpenAICompatibleLLMClient(settings), settings.strip_validation_retries
        )
        self.extract_service = extract_service or ExtractService(
            OpenAICompatibleExtractLLMClient(settings), settings.extract_validation_retries
        )
        self.meaning_service = meaning_service or MeaningService()

    def run(self, source_message: str, context: str | None = None) -> MeaningResult:
        state = THBState()
        canonical = self._stage(
            state,
            WorkflowStage.INPUT,
            lambda: self.input_service(
                TextInputRequest(source_message=source_message, context=context)
            ),
        )
        state.canonical_input = canonical
        stripped = cast(
            StripResult,
            self._stage(
                state,
                WorkflowStage.STRIP,
                lambda: self.strip_service.process(canonical),
            ),
        )
        state.strip_result = stripped
        extracted = cast(
            ExtractResult,
            self._stage(
                state,
                WorkflowStage.EXTRACT,
                lambda: self.extract_service.process(
                    ExtractRequest(canonical_input=canonical, strip_result=stripped)
                ),
            ),
        )
        state.extract_result = extracted
        meaning = cast(
            MeaningResult,
            self._stage(
                state,
                WorkflowStage.MEANING,
                lambda: self.meaning_service.process(extracted),
            ),
        )
        state.meaning_result = meaning
        state.status = WorkflowStatus.COMPLETED
        return meaning

    def _stage(
        self, state: THBState, stage: WorkflowStage, operation: Callable[[], T]
    ) -> T:
        state.current_stage = stage
        started = time.perf_counter()
        try:
            return operation()
        except WorkflowError:
            raise
        except Exception as exc:
            state.status = WorkflowStatus.FAILED
            state.errors.append(str(exc))
            raise WorkflowError(
                f"{stage.value.upper()}_FAILED", stage.value, str(exc), state
            ) from exc
        finally:
            state.stage_durations_ms[stage.value] = (
                time.perf_counter() - started
            ) * 1000
