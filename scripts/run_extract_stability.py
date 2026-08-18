"""Run concurrent multi-round Extract Golden acceptance tests."""

import argparse
import json
import math
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

from thb_input.api.v1.extract import get_extract_service
from thb_input.api.v1.strip import get_strip_service
from thb_input.extract.acceptance import ACCEPTANCE_CASES, ExtractAcceptanceCase
from thb_input.extract.evaluation import evaluate_result
from thb_input.extract.schemas import ExtractRequest
from thb_input.schemas.input import TextInputRequest
from thb_input.services.text_input import build_text_input_record


@dataclass(frozen=True)
class Outcome:
    case: str
    run: int
    structural_passed: bool
    quality_passed: bool
    elapsed_seconds: float
    missing_expected: tuple[str, ...] = ()
    unexpectedly_non_empty: tuple[str, ...] = ()
    error: str | None = None


def run_case(case: ExtractAcceptanceCase, run: int) -> Outcome:
    started = time.perf_counter()
    try:
        canonical = build_text_input_record(
            TextInputRequest(
                source_message=case.source_message,
                context=case.context,
            )
        )
        strip_result = get_strip_service().process(canonical)
        result = get_extract_service().process(
            ExtractRequest(canonical_input=canonical, strip_result=strip_result)
        )
        evaluation = evaluate_result(result, case)
        return Outcome(
            case=case.name,
            run=run,
            structural_passed=True,
            quality_passed=evaluation.passed,
            elapsed_seconds=time.perf_counter() - started,
            missing_expected=tuple(sorted(evaluation.missing_expected)),
            unexpectedly_non_empty=tuple(sorted(evaluation.unexpectedly_non_empty)),
        )
    except Exception as exc:
        return Outcome(
            case=case.name,
            run=run,
            structural_passed=False,
            quality_passed=False,
            elapsed_seconds=time.perf_counter() - started,
            error=f"{type(exc).__name__}: {exc}",
        )


def percentile(values: list[float], percentile_value: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(percentile_value * len(ordered)) - 1)
    return ordered[index]


def build_report(
    outcomes: list[Outcome],
    wall_seconds: float,
    workers: int,
    cases: tuple[ExtractAcceptanceCase, ...],
) -> dict:
    durations = [item.elapsed_seconds for item in outcomes]
    by_case: dict[str, object] = {}
    for case in cases:
        items = [item for item in outcomes if item.case == case.name]
        by_case[case.name] = {
            "runs": len(items),
            "structural_pass_rate": sum(item.structural_passed for item in items)
            / len(items),
            "quality_pass_rate": sum(item.quality_passed for item in items) / len(items),
            "average_seconds": round(
                sum(item.elapsed_seconds for item in items) / len(items), 3
            ),
            "missing_expected": dict(
                Counter(field for item in items for field in item.missing_expected)
            ),
            "unexpectedly_non_empty": dict(
                Counter(field for item in items for field in item.unexpectedly_non_empty)
            ),
            "errors": dict(Counter(item.error for item in items if item.error)),
        }
    return {
        "overall": {
            "workers": workers,
            "runs": len(outcomes),
            "structural_pass_rate": sum(item.structural_passed for item in outcomes)
            / len(outcomes),
            "quality_pass_rate": sum(item.quality_passed for item in outcomes)
            / len(outcomes),
            "wall_seconds": round(wall_seconds, 3),
            "average_case_seconds": round(sum(durations) / len(durations), 3),
            "p95_case_seconds": round(percentile(durations, 0.95), 3),
            "effective_parallelism": round(sum(durations) / wall_seconds, 2),
        },
        "cases": by_case,
        "outcomes": [asdict(item) for item in outcomes],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--only", nargs="*")
    args = parser.parse_args()
    selected_cases = tuple(
        case
        for case in ACCEPTANCE_CASES
        if not args.only or case.name in set(args.only)
    )
    if not selected_cases:
        parser.error("--only did not match any acceptance case")
    jobs = [
        (case, run)
        for run in range(1, args.iterations + 1)
        for case in selected_cases
    ]
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(run_case, case, run) for case, run in jobs]
        outcomes = [future.result() for future in as_completed(futures)]
    report = build_report(
        outcomes,
        time.perf_counter() - started,
        args.workers,
        selected_cases,
    )
    report_name = (
        f"extract-stability-{len(selected_cases)}cases-"
        f"{args.iterations}iterations.json"
    )
    Path("docs", report_name).write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    summary = {"overall": report["overall"], "cases": report["cases"]}
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
