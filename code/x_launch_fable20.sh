#!/bin/bash
# Scratch launcher: Fable leg only, widened to 20 shards (stalls dominate wall-clock; §116).
source /home/matthew/.virtualenvs/pycharm_test/bin/activate
cd "$(dirname "$0")"
for i in $(seq 0 19); do
  JUDGE=claude-fable-5 SHARD=$i/20 python -u -m interp.diagnosis.run_agentic_judge > "../data/interp/diagnosis/agentic-full-fable20-s$i.log" 2>&1 &
done
wait
echo FABLE20-DONE
