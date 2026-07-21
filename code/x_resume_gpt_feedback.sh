#!/bin/bash
# Scratch launcher: resume the blocked GPT feedback leg (decisions section 91) in 4 shards.
cd "$(dirname "$0")"
for i in 0 1 2 3; do
  JUDGE=gpt-5.6-sol CONDITION=feedback SHARD="$i/4" \
    nohup python -m interp.diagnosis.run_judge \
    > "../data/interp/diagnosis/logs/resume-gpt-feedback-$i.log" 2>&1 &
  echo "launched shard $i/4 pid $!"
done
wait
