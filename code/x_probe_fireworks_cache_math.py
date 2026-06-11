import json
import os
import sys
import time
import urllib.error
import urllib.request

API_KEY = os.environ.get("FIREWORKS_API_KEY")
API_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
MODEL_NAME = os.environ.get("FIREWORKS_CACHE_PROBE_MODEL", "deepseek-v4-pro")


def build_model_path(model_name: str) -> str:
    normalized = model_name.replace(".", "p")
    model_path = f"accounts/fireworks/models/{normalized}"

    if normalized == "kimi-k2p5-turbo":
        return "accounts/fireworks/routers/kimi-k2p5-turbo"

    if normalized == "glm-5-fast":
        return "accounts/fireworks/routers/glm-5-fast"

    return model_path


MODEL_PATH = build_model_path(MODEL_NAME)


def build_prompt(variant: str) -> str:
    repeated_block = (
        "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega.\n"
        * 200
    )
    return (
        f"You are a Fireworks cache-math probe variant {variant}. "
        "Reply with exactly OK and nothing else.\n\n"
        + repeated_block
    )


def post_chat_completion(prompt_text: str, prompt_cache_key: str | None = None) -> dict:
    payload = {
        "model": MODEL_PATH,
        "messages": [
            {
                "role": "user",
                "content": prompt_text,
            }
        ],
        "max_tokens": 4,
        "temperature": 0.0,
        "top_p": 1.0,
    }
    if prompt_cache_key is not None:
        payload["prompt_cache_key"] = prompt_cache_key

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {API_KEY or ''}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Fireworks API error {exc.code}: {body}") from exc



def usage_of(response: dict) -> dict:
    usage = response.get("usage", {})
    prompt_tokens_details = usage.get("prompt_tokens_details") or {}
    return {
        "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
        "cached_tokens": int(prompt_tokens_details.get("cached_tokens", 0) or 0),
        "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
        "total_tokens": int(usage.get("total_tokens", 0) or 0),
        "prompt_tokens_details": prompt_tokens_details,
    }



def model_input_tokens(usage: dict) -> int:
    return usage["prompt_tokens"] - usage["cached_tokens"]



def model_total_tokens(usage: dict) -> int:
    return usage["cached_tokens"] + model_input_tokens(usage) + usage["completion_tokens"]



def content_text(response: dict) -> str:
    choices = response.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    return str(message.get("content", ""))



def print_usage(label: str, usage: dict) -> None:
    print(label)
    print(json.dumps(usage, indent=2, sort_keys=True))
    print(
        "model_bucket_total=cached+input+output="
        f"{usage['cached_tokens']} + {model_input_tokens(usage)} + {usage['completion_tokens']}"
        f" = {model_total_tokens(usage)}"
    )
    print(f"model_bucket_total_matches_api_total={model_total_tokens(usage) == usage['total_tokens']}")
    print()



def main() -> int:
    if not API_KEY:
        print("FIREWORKS_API_KEY is not set.", file=sys.stderr)
        return 1

    original_prompt = build_prompt("A")
    invalidated_prompt = build_prompt("B")
    keyed_cache = "fireworks-cache-math-probe-key-1"

    print(f"model_name={MODEL_NAME}")
    print(f"model_path={MODEL_PATH}")
    print(f"original_prompt_chars={len(original_prompt)}")
    print(f"invalidated_prompt_chars={len(invalidated_prompt)}")
    print()

    baseline_no_key = post_chat_completion(original_prompt)
    baseline_no_key_usage = usage_of(baseline_no_key)
    print_usage("baseline_no_key_original", baseline_no_key_usage)
    print(f"baseline_no_key_text={content_text(baseline_no_key)!r}")
    print()

    repeat_no_key = post_chat_completion(original_prompt)
    repeat_no_key_usage = usage_of(repeat_no_key)
    print_usage("repeat_no_key_original", repeat_no_key_usage)
    print(f"repeat_no_key_text={content_text(repeat_no_key)!r}")
    print()

    keyed_first = post_chat_completion(original_prompt, prompt_cache_key=keyed_cache)
    keyed_first_usage = usage_of(keyed_first)
    print_usage("first_with_prompt_cache_key_original", keyed_first_usage)
    print(f"first_with_prompt_cache_key_text={content_text(keyed_first)!r}")
    print()

    time.sleep(1)

    keyed_second = post_chat_completion(original_prompt, prompt_cache_key=keyed_cache)
    keyed_second_usage = usage_of(keyed_second)
    print_usage("second_with_prompt_cache_key_original", keyed_second_usage)
    print(f"second_with_prompt_cache_key_text={content_text(keyed_second)!r}")
    print()

    invalidated_first = post_chat_completion(invalidated_prompt, prompt_cache_key=keyed_cache)
    invalidated_first_usage = usage_of(invalidated_first)
    print_usage("first_with_prompt_cache_key_invalidated", invalidated_first_usage)
    print(f"first_with_prompt_cache_key_invalidated_text={content_text(invalidated_first)!r}")
    print()

    time.sleep(1)

    invalidated_second = post_chat_completion(invalidated_prompt, prompt_cache_key=keyed_cache)
    invalidated_second_usage = usage_of(invalidated_second)
    print_usage("second_with_prompt_cache_key_invalidated", invalidated_second_usage)
    print(f"second_with_prompt_cache_key_invalidated_text={content_text(invalidated_second)!r}")
    print()

    print("comparisons")
    print(f"repeat_no_key_cache_hit_detected={repeat_no_key_usage['cached_tokens'] > 0}")
    print(f"second_with_key_cache_hit_detected={keyed_second_usage['cached_tokens'] > 0}")
    print(
        "invalidated_first_reused_old_cache="
        f"{invalidated_first_usage['cached_tokens'] > 0}"
    )
    print(
        "invalidated_second_cache_hit_detected="
        f"{invalidated_second_usage['cached_tokens'] > 0}"
    )
    print(
        "cause_hint="
        + (
            "prompt_cache_key improves session affinity but is not strictly required for immediate repeat hits"
            if repeat_no_key_usage["cached_tokens"] > 0 and keyed_second_usage["cached_tokens"] > 0
            else "cache hits only appeared with prompt_cache_key, suggesting affinity is the cause"
            if repeat_no_key_usage["cached_tokens"] == 0 and keyed_second_usage["cached_tokens"] > 0
            else "no cache hits appeared even with prompt_cache_key, suggesting model/support/workload constraints"
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

