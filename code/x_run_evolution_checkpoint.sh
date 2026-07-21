#!/bin/bash
# Scratch launcher: D2 evolution-condition first-10 checkpoint (5 modular episodes x 3 judges).
cd "$(dirname "$0")"
for judge in gpt-5.6-sol claude-fable-5 gemini-3.1-pro-preview; do
  JUDGE="$judge" CONDITION=evolution \
    nohup python -m interp.diagnosis.run_judge \
    > "../data/interp/diagnosis/logs/evolution-checkpoint-$judge.log" 2>&1 &
  echo "launched $judge pid $!"
done
wait
echo "checkpoint complete"
