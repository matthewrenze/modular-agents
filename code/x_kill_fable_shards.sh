#!/bin/bash
# Scratch: kill only the Fable agentic-judge shard processes (identified by stdout log path).
killed=0
for pid in $(pgrep -f run_agentic_judge); do
  target=$(readlink /proc/$pid/fd/1 2>/dev/null)
  case $target in *fable*) kill $pid 2>/dev/null; killed=$((killed+1));; esac
done
echo "killed $killed fable shards"
sleep 2
remaining=0
for pid in $(pgrep -f run_agentic_judge); do
  target=$(readlink /proc/$pid/fd/1 2>/dev/null)
  case $target in *fable*) remaining=$((remaining+1));; esac
done
echo "$remaining fable shards remaining"
