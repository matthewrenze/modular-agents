import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from log import Log

# Reproducibility caveat: exact regeneration requires textworld==1.6.2. The treasure
# and cooking generators bump the seed by +100 on bad-map errors (plus a task 3-94 hack),
# so the realized seeds depend on TextWorld's internal generation behavior.

# Set parameters
MAX_WORKERS = 12

# Create log
log = Log("all")

# Create the commands
commands = [

    # Simple (one process per set)
    ["create_tw_simple.py", "--set", "train"],
    ["create_tw_simple.py", "--set", "test"],

    # Treasure levels 1-2 (one process per set/level)
    ["create_tw_treasure.py", "--set", "train", "--level", "1"],
    ["create_tw_treasure.py", "--set", "train", "--level", "2"],
    ["create_tw_treasure.py", "--set", "test",  "--level", "1"],
    ["create_tw_treasure.py", "--set", "test",  "--level", "2"],

    # Treasure level 3 (one process per task — slow, benefits from individual processes)
    *[["create_tw_treasure.py", "--set", s, "--level", "3", "--start", str(i), "--end", str(i)]
      for s in ["train", "test"] for i in range(1, 101)],

    # Coin (one process per set/level)
    ["create_tw_coin.py", "--set", "train", "--level", "1"],
    ["create_tw_coin.py", "--set", "train", "--level", "2"],
    ["create_tw_coin.py", "--set", "train", "--level", "3"],
    ["create_tw_coin.py", "--set", "test",  "--level", "1"],
    ["create_tw_coin.py", "--set", "test",  "--level", "2"],
    ["create_tw_coin.py", "--set", "test",  "--level", "3"],

    # Cooking (one process per set/level)
    ["create_tw_cooking.py", "--set", "train", "--level", "1"],
    ["create_tw_cooking.py", "--set", "train", "--level", "2"],
    ["create_tw_cooking.py", "--set", "train", "--level", "3"],
    ["create_tw_cooking.py", "--set", "test",  "--level", "1"],
    ["create_tw_cooking.py", "--set", "test",  "--level", "2"],
    ["create_tw_cooking.py", "--set", "test",  "--level", "3"],

    # Quick eval (reads from existing cooking JSONL files)
    ["create_tw_quick.py", "--set", "train"],
    ["create_tw_quick.py", "--set", "test"],
]


def run_command(cmd):
    result = subprocess.run([sys.executable] + cmd)
    return cmd, result.returncode


log.write(f"\nRunning {len(commands)} tasks with {MAX_WORKERS} workers...\n")

failures = []
with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(run_command, cmd): cmd for cmd in commands}
    completed = 0
    for future in as_completed(futures):
        cmd, returncode = future.result()
        completed += 1
        if returncode != 0:
            failures.append(cmd)
            log.write(f"[{completed}/{len(commands)}] ERROR: {' '.join(cmd)}")
        else:
            log.write(f"[{completed}/{len(commands)}] Done: {' '.join(cmd)}")

if failures:
    log.write(f"\n{len(failures)} task(s) failed:")
    for cmd in failures:
        log.write(f"  {' '.join(cmd)}")
    sys.exit(1)

log.write("\n=== All done! ===\n")
