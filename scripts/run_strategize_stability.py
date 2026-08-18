"""Run concurrent multi-round Strategize Golden acceptance tests."""

import argparse
import json
import math
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

from thb_input.api.v1.strategize import get_strategize_service
from thb_input.strategize.acceptance import ACCEPTANCE_CASES, StrategizeAcceptanceCase
from thb_input.strategize.evaluation import evaluate_result
from thb_input.strategize.schemas import StrategizeRequest, UserGoalInput


@dataclass(frozen=True)
class Outcome:
    case: str
    run: int
    structural_passed: bool
    quality_passed: bool
    elapsed_seconds: float
    missing_types: tuple[str, ...] = ()
    forbidden_types: tuple[str, ...] = ()
    missing_required_user_input: bool = False
    error: str | None = None


def run_case(case: StrategizeAcceptanceCase, run: int) -> Outcome:
    started = time.perf_counter()
    try:
        result = get_strategize_service().process(
            StrategizeRequest(
                extract_result=case.extract_result,
                user_goal=(
                    UserGoalInput(content=case.explicit_goal)
                    if case.explicit_goal
                    else None
                ),
                context=None,
            )
        )
        evaluation = evaluate_result(result, case)
        return Outcome(
            case=case.name,
            run=run,
            structural_passed=True,
            quality_passed=evaluation.passed,
            elapsed_seconds=time.perf_counter() - started,
            missing_types=tuple(sorted(item.value for item in evaluation.missing_types)),
            forbidden_types=tuple(
                sorted(item.value for item in evaluation.forbidden_types)
            ),
            missing_required_user_input=evaluation.missing_required_user_input,
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


def _percentile(values: list[float], value: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(value * len(ordered)) - 1)]


def build_report(
    outcomes: list[Outcome],
    wall_seconds: float,
    workers: int,
    cases_to_report: tuple[StrategizeAcceptanceCase, ...],
) -> dict:
    durations = [item.elapsed_seconds for item in outcomes]
    cases: dict[str, object] = {}
    for case in cases_to_report:
        items = [item for item in outcomes if item.case == case.name]
        cases[case.name] = {
            "runs": len(items),
            "structural_pass_rate": sum(item.structural_passed for item in items)
            / len(items),
            "quality_pass_rate": sum(item.quality_passed for item in items) / len(items),
            "average_seconds": round(
                sum(item.elapsed_seconds for item in items) / len(items), 3
            ),
            "missing_types": dict(
                Counter(value for item in items for value in item.missing_types)
            ),
            "forbidden_types": dict(
                Counter(value for item in items for value in item.forbidden_types)
            ),
            "missing_required_user_input": sum(
                item.missing_required_user_input for item in items
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
            "p95_case_seconds": round(_percentile(durations, 0.95), 3),
            "effective_parallelism": round(sum(durations) / wall_seconds, 2),
        },
        "cases": cases,
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
        f"strategize-stability-{len(selected_cases)}cases-"
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
