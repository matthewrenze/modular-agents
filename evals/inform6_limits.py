"""Inform 6 memory-limit workaround for long TextWorld games.

At recipe >= 8 the cooking compile fails with `MAX_EXPRESSION_NODES (256) exceeded`.
The `$MAX_EXPRESSION_NODES=` command-line fix named in that error message DOES NOT
WORK: Inform 7 writes its own `!%` settings header into auto.inf, and that header
overrides the command line. The fix is to rewrite the header just before inform6
runs. Recipe and evidence: evals/x_probe_long_lengths.py (verified 2026-07-26).
"""
import re
import subprocess

# Inform 7 writes these into auto.inf's `!%` header; the values there beat the command line
INFORM6_LIMITS = {
    "MAX_EXPRESSION_NODES": 4000,
    "MAX_STATIC_DATA": 8000000,
    "MAX_PROP_TABLE_SIZE": 2000000,
    "MAX_SYMBOLS": 80000,
    "MAX_LABELS": 400000,
    "MAX_ARRAYS": 40000,
    "MAX_ZCODE_SIZE": 4000000,
    "MAX_INDIV_PROP_TABLE_SIZE": 400000,
    "MAX_OBJECTS": 4000,
}


def rewrite_limits_header(text: str, limits: dict) -> str:
    """Override the `!% $NAME=value` settings in auto.inf's header; append any missing ones."""
    header, separator, body = text.partition("\n\n")

    # Raise every limit that is already set in the header
    header = re.sub(
        r"!%\s*\$(\w+)=\d+",
        lambda m: f"!% ${m.group(1)}={limits[m.group(1)]}"
        if m.group(1) in limits else m.group(0),
        header)

    # Append the limits the header does not set yet
    already_set = set(re.findall(r"!%\s*\$(\w+)=", header))
    missing = "\n".join(f"!% ${name}={value}" for name, value in limits.items()
                        if name not in already_set)
    if missing:
        header += "\n" + missing

    return header + separator + body


def patch_inform6_limits():
    """Rewrite auto.inf's `!%` header immediately before inform6 runs.

    NOTE: replaces subprocess.check_output process-wide (world2inform7 imports the
    shared subprocess module) — call once, from a generation script only.
    """
    original = subprocess.check_output

    def check_output(cmd, *args, **kwargs):
        if isinstance(cmd, list) and cmd and "inform6" in str(cmd[0]):
            source_path = cmd[2]
            with open(source_path, "r", errors="replace") as file:
                text = file.read()
            with open(source_path, "w") as file:
                file.write(rewrite_limits_header(text, INFORM6_LIMITS))
        return original(cmd, *args, **kwargs)

    subprocess.check_output = check_output
