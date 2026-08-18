import argparse
import json
import math
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from thb_input.config import Settings
from thb_input.schemas.input import TextInputRequest
from thb_input.services.text_input import build_text_input_record
from thb_input.strip.acceptance import GOLDEN_CASES, LONG_CASES, GoldenCase
from thb_input.strip.evaluation import evaluate_labels
from thb_input.strip.llm import LLMClient, OpenAICompatibleLLMClient
from thb_input.strip.service import StripService


class CountingClient:
    def __init__(self, inner: LLMClient) -> None:
        self.inner = inner
        self.calls = 0

    def complete_structured(self, prompt: object) -> object:
        self.calls += 1
        return self.inner.complete_structured(prompt)


@dataclass(frozen=True)
class Outcome:
    case_name: str
    structural_pass: bool
    quality_pass: bool
    attempts: int
    elapsed: float
    fingerprint: tuple[str, ...]
    error_code: str | None
    missing_required: tuple[str, ...]
    unexpected: tuple[str, ...]
    forbidden_detected: tuple[str, ...]
    missing_required_any: tuple[str, ...]
    error_message: str | None


def run_case(case: GoldenCase, settings: Settings) -> Outcome:
    client = CountingClient(OpenAICompatibleLLMClient(settings))
    service = StripService(client, validation_retries=settings.strip_validation_retries)
    canonical_input = build_text_input_record(
        TextInputRequest(source_message=case.source_message, context=case.context)
    )
    started_at = time.perf_counter()
    try:
        result = service.process(canonical_input)
        evaluation = evaluate_labels(result, case.expectation)
        fingerprint = tuple(sorted(label.value for label in result.summary.detected_labels))
        return Outcome(
            case.name,
            True,
            evaluation.passed,
            client.calls,
            time.perf_counter() - started_at,
            fingerprint,
            None,
            tuple(sorted(label.value for label in evaluation.missing_required)),
            tuple(sorted(label.value for label in evaluation.unexpected)),
            tuple(sorted(label.value for label in evaluation.forbidden_detected)),
            tuple(
                "|".join(sorted(label.value for label in group))
                for group in evaluation.missing_required_any
            ),
            None,
        )
    except Exception as exc:
        code = getattr(getattr(exc, "code", None), "value", type(exc).__name__)
        return Outcome(
            case.name,
            False,
            False,
            client.calls,
            time.perf_counter() - started_at,
            (),
            str(code),
            (),
            (),
            (),
            (),
            str(exc),
        )


def percentile_95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]


parser = argparse.ArgumentParser(description="Run Strip stability acceptance tests.")
parser.add_argument("--env-file", default=".env")
parser.add_argument("--iterations", type=int, default=5)
parser.add_argument("--workers", type=int, default=3)
parser.add_argument("--include-long", action="store_true")
parser.add_argument("--only", nargs="*", default=[])
args = parser.parse_args()

settings = Settings(_env_file=args.env_file)
cases = GOLDEN_CASES + (LONG_CASES if args.include_long else ())
if args.only:
    cases = tuple(case for case in cases if case.name in args.only)
jobs = [(case, iteration) for case in cases for iteration in range(args.iterations)]
outcomes = []

with ThreadPoolExecutor(max_workers=args.workers) as executor:
    futures = [executor.submit(run_case, case, settings) for case, _ in jobs]
    for future in as_completed(futures):
        outcomes.append(future.result())

grouped = defaultdict(list)
for outcome in outcomes:
    grouped[outcome.case_name].append(outcome)

case_reports = {}
for case_name, items in sorted(grouped.items()):
    structural = [item for item in items if item.structural_pass]
    fingerprints = Counter(item.fingerprint for item in structural)
    case_reports[case_name] = {
        "runs": len(items),
        "first_pass_rate": sum(item.structural_pass and item.attempts == 1 for item in items)
        / len(items),
        "final_pass_rate": len(structural) / len(items),
        "quality_pass_rate": sum(item.quality_pass for item in items) / len(items),
        "label_consistency": (
            fingerprints.most_common(1)[0][1] / len(structural) if structural else 0.0
        ),
        "average_attempts": sum(item.attempts for item in items) / len(items),
        "average_latency_seconds": sum(item.elapsed for item in items) / len(items),
        "p95_latency_seconds": percentile_95([item.elapsed for item in items]),
        "errors": dict(Counter(item.error_code for item in items if item.error_code)),
        "error_messages": dict(
            Counter(item.error_message for item in items if item.error_message)
        ),
        "missing_required": dict(
            Counter(label for item in items for label in item.missing_required)
        ),
        "unexpected": dict(Counter(label for item in items for label in item.unexpected)),
        "forbidden_detected": dict(
            Counter(label for item in items for label in item.forbidden_detected)
        ),
        "missing_required_any": dict(
            Counter(group for item in items for group in item.missing_required_any)
        ),
    }

overall = {
    "runs": len(outcomes),
    "first_pass_rate": sum(item.structural_pass and item.attempts == 1 for item in outcomes)
    / len(outcomes),
    "final_pass_rate": sum(item.structural_pass for item in outcomes) / len(outcomes),
    "quality_pass_rate": sum(item.quality_pass for item in outcomes) / len(outcomes),
    "average_attempts": sum(item.attempts for item in outcomes) / len(outcomes),
    "average_latency_seconds": sum(item.elapsed for item in outcomes) / len(outcomes),
    "p95_latency_seconds": percentile_95([item.elapsed for item in outcomes]),
}

print(json.dumps({"overall": overall, "cases": case_reports}, indent=2))
