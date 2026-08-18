import argparse
import json
import time

from thb_input.config import Settings
from thb_input.schemas.input import TextInputRequest
from thb_input.services.text_input import build_text_input_record
from thb_input.strip.llm import OpenAICompatibleLLMClient
from thb_input.strip.service import StripService

parser = argparse.ArgumentParser(description="Run a live THB Strip connection test.")
parser.add_argument("--env-file", default=".env")
args = parser.parse_args()

settings = Settings(_env_file=args.env_file)
canonical_input = build_text_input_record(
    TextInputRequest(source_message="文件我已经发给你了，请今天确认一下。")
)

started_at = time.perf_counter()
result = StripService(OpenAICompatibleLLMClient(settings)).process(canonical_input)
elapsed_seconds = time.perf_counter() - started_at

print(f"CONNECTION_TEST: PASSED ({elapsed_seconds:.2f}s)")
print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
