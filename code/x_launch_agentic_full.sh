#!/bin/bash
# Scratch launcher for the full agentic-judge sweep (avoids wsl.exe $-mangling, decisions section 98).
# Fable 10 shards, GPT 4 shards, Gemini 4 shards; all resumable; logs per shard.
source /home/matthew/.virtualenvs/pycharm_test/bin/activate
cd "$(dirname "$0")"
for i in 0 1 2 3 4 5 6 7 8 9; do
  JUDGE=claude-fable-5 SHARD=$i/10 python -u -m interp.diagnosis.run_agentic_judge > "../data/interp/diagnosis/agentic-full-fable-s$i.log" 2>&1 &
done
for i in 0 1 2 3; do
  JUDGE=gpt-5.6-sol SHARD=$i/4 python -u -m interp.diagnosis.run_agentic_judge > "../data/interp/diagnosis/agentic-full-gpt-s$i.log" 2>&1 &
done
for i in 0 1 2 3; do
  JUDGE=gemini-3.1-pro-preview SHARD=$i/4 python -u -m interp.diagnosis.run_agentic_judge > "../data/interp/diagnosis/agentic-full-gemini-s$i.log" 2>&1 &
done
wait
echo ALL-LEGS-DONE
