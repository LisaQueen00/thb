"""Measure five concurrent Input -> Strip -> Extract test pipelines."""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from thb_input.api.v1.extract import get_extract_service
from thb_input.api.v1.strip import get_strip_service
from thb_input.extract.acceptance import ACCEPTANCE_CASES
from thb_input.extract.schemas import ExtractRequest
from thb_input.schemas.input import TextInputRequest
from thb_input.services.text_input import build_text_input_record


@dataclass(frozen=True)
class Outcome:
    name: str
    passed: bool
    elapsed_seconds: float
    error: str | None


def run_case(name: str, source_message: str, context: str | None) -> Outcome:
    started = time.perf_counter()
    try:
        canonical = build_text_input_record(
            TextInputRequest(source_message=source_message, context=context)
        )
        strip_result = get_strip_service().process(canonical)
        get_extract_service().process(
            ExtractRequest(canonical_input=canonical, strip_result=strip_result)
        )
        return Outcome(name, True, time.perf_counter() - started, None)
    except Exception as exc:
        return Outcome(
            name,
            False,
            time.perf_counter() - started,
            f"{type(exc).__name__}: {exc}",
        )


def main() -> None:
    cases = ACCEPTANCE_CASES[:5]
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(
                run_case,
                case.name,
                case.source_message,
                case.context,
            ): case.name
            for case in cases
        }
        outcomes = [future.result() for future in as_completed(futures)]
    wall_seconds = time.perf_counter() - started
    serial_equivalent = sum(outcome.elapsed_seconds for outcome in outcomes)
    report = {
        "configured_concurrency": 5,
        "test_count": len(outcomes),
        "passed": sum(outcome.passed for outcome in outcomes),
        "failed": sum(not outcome.passed for outcome in outcomes),
        "wall_seconds": round(wall_seconds, 3),
        "sum_individual_seconds": round(serial_equivalent, 3),
        "effective_parallelism": round(serial_equivalent / wall_seconds, 2),
        "estimated_time_saved_percent": round(
            (1 - wall_seconds / serial_equivalent) * 100,
            1,
        ),
        "cases": [
            {
                "name": outcome.name,
                "passed": outcome.passed,
                "elapsed_seconds": round(outcome.elapsed_seconds, 3),
                "error": outcome.error,
            }
            for outcome in sorted(outcomes, key=lambda item: item.name)
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
