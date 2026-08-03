#!/bin/bash
# k-sweep wave launcher: one window per (agent x eval), 10 episodes sequential per window,
# all windows parallel. Run inside WSL via: wsl.exe -- bash -lc 'bash <this file>'
# (login shell loads API keys). Proven in Waves 1-2: 20-way on OpenAI Tier 5, no throttling.
# Edit AGENTS per wave. Wave 3 = "modular-kn" only (10 windows).
AGENTS="modular-kn"
EVALS="tw-simple-1 tw-treasure-1 tw-treasure-2 tw-treasure-3 tw-coin-1 tw-coin-2 tw-coin-3 tw-cooking-1 tw-cooking-2 tw-cooking-3"
REPO="/mnt/c/Users/Matthew/Dropbox/Professional/Research/Projects/Modular Agents/Repositories/modular-agents-kn"
LOGDIR="$REPO/data/logs/wave3"

source /home/matthew/.virtualenvs/pycharm_test/bin/activate
cd "$REPO/code"
mkdir -p "$LOGDIR"
for agent in $AGENTS; do
  for ev in $EVALS; do
    nohup bash -c "for ep in 10 20 30 40 50 60 70 80 90 100; do python run_episode.py --split test --model gpt-5.4 --agent $agent --eval $ev --episode \$ep; done; echo WINDOW_DONE" > "$LOGDIR/$agent-$ev.log" 2>&1 &
    sleep 2
  done
done
wait
echo "ALL_WINDOWS_COMPLETE"
