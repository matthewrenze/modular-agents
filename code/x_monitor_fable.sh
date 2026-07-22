#!/bin/bash
# Scratch: 5-minute ticker on the Fable agentic-judge re-run; exits when all shards exit.
cd "/mnt/c/Users/Matthew/Dropbox/Professional/Research/Projects/Modular Agents/Repositories/modular-agents-dev/data/interp/diagnosis/agentic-judge"
while true; do
  n=$(ls claude-fable-5 | wc -l)
  p=$(pgrep -fc run_agentic_judge)
  echo "fable $n/242, $p shard(s) running"
  if [ "$p" -eq 0 ]; then
    echo "DONE-ALL-SHARDS-EXITED"
    break
  fi
  sleep 300
done
