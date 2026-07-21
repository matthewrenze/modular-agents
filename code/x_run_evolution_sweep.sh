#!/bin/bash
# Scratch launcher: D2 evolution-condition FULL sweep (126 modular episodes x 3 judges).
# Provider-parallel; Gemini split into 3 disjoint shards (Phase C hang pattern, decisions
# section 80/82). Resumable: already-judged D2 records (incl. the 5 checkpoint episodes)
# are skipped by run_judge.py.
cd "$(dirname "$0")"
LOGS="../data/interp/diagnosis/logs"

JUDGE=gpt-5.6-sol CONDITION=evolution \
  nohup python -m interp.diagnosis.run_judge > "$LOGS/evolution-sweep-gpt-5.6-sol.log" 2>&1 &
echo "launched gpt-5.6-sol pid $!"

JUDGE=claude-fable-5 CONDITION=evolution \
  nohup python -m interp.diagnosis.run_judge > "$LOGS/evolution-sweep-claude-fable-5.log" 2>&1 &
echo "launched claude-fable-5 pid $!"

for i in 0 1 2; do
  JUDGE=gemini-3.1-pro-preview CONDITION=evolution SHARD="$i/3" \
    nohup python -m interp.diagnosis.run_judge > "$LOGS/evolution-sweep-gemini-shard-$i.log" 2>&1 &
  echo "launched gemini-3.1-pro-preview shard $i/3 pid $!"
done
wait
echo "sweep complete"
