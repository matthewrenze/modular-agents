#!/bin/bash
# Scratch: third pass on the 10 residual malformed agentic-judge records.
# Deletes the malformed record JSONs, then re-runs the two affected judges
# (skip logic re-judges only the missing records).
cd "/mnt/c/Users/Matthew/Dropbox/Professional/Research/Projects/Modular Agents/Repositories/modular-agents-dev"
source /home/matthew/.virtualenvs/pycharm_test/bin/activate

A="data/interp/diagnosis/agentic-judge"
rm -v "$A/claude-fable-5/claude-sonnet-4-6--modular-full--tw-coin-2--episode-70.json"
rm -v "$A/gemini-3.1-pro-preview/claude-sonnet-4-6--modular-full--tw-coin-2--episode-80.json"
rm -v "$A/gemini-3.1-pro-preview/deepseek-v4-pro--modular-full--tw-coin-2--episode-100.json"
rm -v "$A/gemini-3.1-pro-preview/deepseek-v4-pro--modular-full--tw-coin-3--episode-80.json"
rm -v "$A/gemini-3.1-pro-preview/gpt-5.2--react-kn--tw-coin-3--episode-30.json"
rm -v "$A/gemini-3.1-pro-preview/minimax-m3--modular-full--tw-coin-1--episode-100.json"
rm -v "$A/gemini-3.1-pro-preview/minimax-m3--modular-full--tw-coin-3--episode-100.json"
rm -v "$A/gemini-3.1-pro-preview/minimax-m3--react-kn--tw-coin-3--episode-80.json"
rm -v "$A/gemini-3.1-pro-preview/nemotron-3-ultra--modular-full--tw-coin-3--episode-90.json"
rm -v "$A/gemini-3.1-pro-preview/nemotron-3-ultra--react-kn--tw-coin-1--episode-60.json"

cd code
JUDGE=claude-fable-5 python -m interp.diagnosis.run_agentic_judge > ../data/interp/diagnosis/agentic-residue-fable.log 2>&1 &
JUDGE=gemini-3.1-pro-preview python -m interp.diagnosis.run_agentic_judge > ../data/interp/diagnosis/agentic-residue-gemini.log 2>&1 &
wait
echo "RESIDUE-PASS-DONE"
