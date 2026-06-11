import json
import os
import sys
import time
import urllib.error
import urllib.request

MODEL = os.environ.get("CLAUDE_CACHE_PROBE_MODEL", "claude-sonnet-4-6")
API_KEY = os.environ.get("ANTHROPIC_KEY")
API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


def build_long_prefix(variant: str) -> str:
    return (
        f"You are a cache-math probe variant {variant}. Read the following reference text and answer with exactly OK.\n\n"
        + (
            "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega.\n"
            * 180
        )
    )

MESSAGES = [
    {
        "role": "user",
        "content": "Reply with exactly OK and nothing else.",
    }
]


def post_message(use_cache: bool, system_text: str) -> dict:
    payload = {
        "model": MODEL,
        "max_tokens": 4,
        "temperature": 0,
        "system": system_text,
        "messages": MESSAGES,
    }
    if use_cache:
        payload["cache_control"] = {"type": "ephemeral"}

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=data,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": API_KEY or "",
            "anthropic-version": ANTHROPIC_VERSION,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Anthropic API error {exc.code}: {body}"
        ) from exc


def usage_of(response: dict) -> dict:
    usage = response.get("usage", {})
    return {
        "input_tokens": int(usage.get("input_tokens", 0) or 0),
        "cache_creation_input_tokens": int(usage.get("cache_creation_input_tokens", 0) or 0),
        "cache_read_input_tokens": int(usage.get("cache_read_input_tokens", 0) or 0),
        "output_tokens": int(usage.get("output_tokens", 0) or 0),
        "api_total_tokens": int(usage.get("total_tokens", 0) or 0) if usage.get("total_tokens") is not None else None,
    }


def prompt_side_total(usage: dict) -> int:
    return (
        usage["input_tokens"]
        + usage["cache_creation_input_tokens"]
        + usage["cache_read_input_tokens"]
    )


def model_cached_tokens(usage: dict) -> int:
    return usage["cache_read_input_tokens"]


def model_input_tokens(usage: dict) -> int:
    return usage["input_tokens"] + usage["cache_creation_input_tokens"]


def model_total_tokens(usage: dict) -> int:
    return model_cached_tokens(usage) + model_input_tokens(usage) + usage["output_tokens"]


def raw_three_field_total(usage: dict) -> int:
    return usage["cache_read_input_tokens"] + usage["input_tokens"] + usage["output_tokens"]


def content_text(response: dict) -> str:
    parts = response.get("content", [])
    if not parts:
        return ""
    first = parts[0]
    if isinstance(first, dict):
        return str(first.get("text", ""))
    return str(first)


def print_usage(label: str, usage: dict) -> None:
    print(label)
    print(json.dumps(usage, indent=2, sort_keys=True))
    print(f"prompt_side_total={prompt_side_total(usage)}")
    print(f"raw_three_field_total=cached_read+input+output={raw_three_field_total(usage)}")
    print(
        "model_bucket_total=cached+input+output="
        f"{model_cached_tokens(usage)} + {model_input_tokens(usage)} + {usage['output_tokens']}"
        f" = {model_total_tokens(usage)}"
    )
    if usage["api_total_tokens"] is None:
        print("api_total_tokens=missing")
    else:
        print(f"api_total_tokens={usage['api_total_tokens']}")
        print(f"model_bucket_total_matches_api_total={model_total_tokens(usage) == usage['api_total_tokens']}")
    print()


def main() -> int:
    if not API_KEY:
        print("ANTHROPIC_KEY is not set.", file=sys.stderr)
        return 1

    original_prefix = build_long_prefix("A")
    invalidated_prefix = build_long_prefix("B")

    print(f"model={MODEL}")
    print(f"original_system_chars={len(original_prefix)}")
    print(f"invalidated_system_chars={len(invalidated_prefix)}")
    print()

    baseline = post_message(use_cache=False, system_text=original_prefix)
    baseline_usage = usage_of(baseline)
    print_usage("baseline_no_cache_original", baseline_usage)
    print(f"baseline_text={content_text(baseline)!r}")
    print()

    first_cached = post_message(use_cache=True, system_text=original_prefix)
    first_cached_usage = usage_of(first_cached)
    print_usage("first_cached_request_original", first_cached_usage)
    print(f"first_cached_text={content_text(first_cached)!r}")
    print()

    time.sleep(1)

    second_cached = post_message(use_cache=True, system_text=original_prefix)
    second_cached_usage = usage_of(second_cached)
    print_usage("second_cached_request_original", second_cached_usage)
    print(f"second_cached_text={content_text(second_cached)!r}")
    print()

    invalidated_baseline = post_message(use_cache=False, system_text=invalidated_prefix)
    invalidated_baseline_usage = usage_of(invalidated_baseline)
    print_usage("baseline_no_cache_invalidated", invalidated_baseline_usage)
    print(f"invalidated_baseline_text={content_text(invalidated_baseline)!r}")
    print()

    invalidated_first_cached = post_message(use_cache=True, system_text=invalidated_prefix)
    invalidated_first_cached_usage = usage_of(invalidated_first_cached)
    print_usage("first_cached_request_invalidated", invalidated_first_cached_usage)
    print(f"invalidated_first_cached_text={content_text(invalidated_first_cached)!r}")
    print()

    time.sleep(1)

    invalidated_second_cached = post_message(use_cache=True, system_text=invalidated_prefix)
    invalidated_second_cached_usage = usage_of(invalidated_second_cached)
    print_usage("second_cached_request_invalidated", invalidated_second_cached_usage)
    print(f"invalidated_second_cached_text={content_text(invalidated_second_cached)!r}")
    print()

    baseline_total = baseline_usage["input_tokens"] + baseline_usage["output_tokens"]
    invalidated_baseline_total = invalidated_baseline_usage["input_tokens"] + invalidated_baseline_usage["output_tokens"]
    print("comparisons")
    print(f"baseline_total_no_cache_original={baseline_total}")
    print(
        "first_cached_total_original="
        f"cached {model_cached_tokens(first_cached_usage)} + input {model_input_tokens(first_cached_usage)} + output {first_cached_usage['output_tokens']}"
        f" = {model_total_tokens(first_cached_usage)}"
    )
    print(
        "second_cached_total_original="
        f"cached {model_cached_tokens(second_cached_usage)} + input {model_input_tokens(second_cached_usage)} + output {second_cached_usage['output_tokens']}"
        f" = {model_total_tokens(second_cached_usage)}"
    )
    print(f"baseline_total_no_cache_invalidated={invalidated_baseline_total}")
    print(
        "first_cached_total_invalidated="
        f"cached {model_cached_tokens(invalidated_first_cached_usage)} + input {model_input_tokens(invalidated_first_cached_usage)} + output {invalidated_first_cached_usage['output_tokens']}"
        f" = {model_total_tokens(invalidated_first_cached_usage)}"
    )
    print(
        "second_cached_total_invalidated="
        f"cached {model_cached_tokens(invalidated_second_cached_usage)} + input {model_input_tokens(invalidated_second_cached_usage)} + output {invalidated_second_cached_usage['output_tokens']}"
        f" = {model_total_tokens(invalidated_second_cached_usage)}"
    )
    print()

    if first_cached_usage["cache_creation_input_tokens"] > 0:
        print("first_request_cache_creation_detected=yes")
    else:
        print("first_request_cache_creation_detected=no")

    if second_cached_usage["cache_read_input_tokens"] > 0:
        print("second_request_cache_read_detected=yes")
    else:
        print("second_request_cache_read_detected=no")

    if model_total_tokens(first_cached_usage) == baseline_total:
        print("first_request_total_matches_original_baseline=yes")
    else:
        print("first_request_total_matches_original_baseline=no")

    if model_total_tokens(second_cached_usage) == baseline_total:
        print("second_request_total_matches_original_baseline=yes")
    else:
        print("second_request_total_matches_original_baseline=no")

    if invalidated_first_cached_usage["cache_read_input_tokens"] == 0 and invalidated_first_cached_usage["cache_creation_input_tokens"] > 0:
        print("invalidated_first_request_reused_old_cache=no")
    else:
        print("invalidated_first_request_reused_old_cache=yes")

    if model_total_tokens(invalidated_first_cached_usage) == invalidated_baseline_total:
        print("invalidated_first_request_total_matches_invalidated_baseline=yes")
    else:
        print("invalidated_first_request_total_matches_invalidated_baseline=no")

    if invalidated_second_cached_usage["cache_read_input_tokens"] > 0:
        print("invalidated_second_request_cache_read_detected=yes")
    else:
        print("invalidated_second_request_cache_read_detected=no")

    if model_total_tokens(invalidated_second_cached_usage) == invalidated_baseline_total:
        print("invalidated_second_request_total_matches_invalidated_baseline=yes")
    else:
        print("invalidated_second_request_total_matches_invalidated_baseline=no")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

