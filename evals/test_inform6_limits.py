"""Unit tests for the auto.inf `!%` header rewrite (no TextWorld needed).

Run from evals/: python -m pytest -q
"""
from inform6_limits import rewrite_limits_header

LIMITS = {"MAX_EXPRESSION_NODES": 4000, "MAX_STATIC_DATA": 8000000}

TEXT = (
    "!% $MAX_EXPRESSION_NODES=256\n"
    "!% $MAX_UNRELATED_SETTING=123\n"
    "!% -~S\n"
    "\n"
    "! The body starts here\n"
    "Constant MAX_EXPRESSION_NODES 999; ! decoy in the body\n")


def test_overrides_existing_setting():
    result = rewrite_limits_header(TEXT, LIMITS)
    assert "!% $MAX_EXPRESSION_NODES=4000" in result
    assert "!% $MAX_EXPRESSION_NODES=256" not in result


def test_preserves_unrelated_settings_and_flags():
    result = rewrite_limits_header(TEXT, LIMITS)
    assert "!% $MAX_UNRELATED_SETTING=123" in result
    assert "!% -~S" in result


def test_appends_missing_settings_to_header():
    result = rewrite_limits_header(TEXT, LIMITS)
    header = result.partition("\n\n")[0]
    assert "!% $MAX_STATIC_DATA=8000000" in header


def test_body_is_untouched():
    result = rewrite_limits_header(TEXT, LIMITS)
    body = result.partition("\n\n")[2]
    assert body == TEXT.partition("\n\n")[2]
