# Post-wave verification. Run in WSL AFTER backing up data/summaries.csv and running
# 2_summarize_results.py. Checks the v6.0 baseline rows survived regeneration unchanged
# and prints per-arm totals. Edit NEW_ARMS and BACKUP per wave.
import pandas as pd

DATA = "/mnt/c/Users/Matthew/Dropbox/Professional/Research/Projects/Modular Agents/Repositories/modular-agents-kn/data"
BACKUP = f"{DATA}/summaries-backup-pre-wave1-20260802.csv"  # any pre-wave backup holding the baseline rows
NEW_ARMS = ["react-k10", "modular-k10"]

new = pd.read_csv(f"{DATA}/summaries.csv")
old = pd.read_csv(BACKUP)

key = ["version", "split_name", "model_name", "agent_name", "eval_name"]
base_agents = ["modular-full", "react-k1", "react-kn"]
mask = lambda df: df[(df.version == "v6.0") & (df.split_name == "test") &
                     (df.model_name == "gpt-5.4") & (df.agent_name.isin(base_agents))]
o = mask(old).sort_values(key).reset_index(drop=True)
n = mask(new).sort_values(key).reset_index(drop=True)
common_cols = [c for c in o.columns if c in n.columns]
same = o[common_cols].astype(str).equals(n[common_cols].astype(str))
print(f"baseline rows: old={len(o)} new={len(n)} identical={same}")

t = new[(new.split_name == "test") & (new.model_name == "gpt-5.4")]
for a in base_agents + NEW_ARMS:
    rows = t[t.agent_name == a]
    if len(rows):
        print(f"{a}: evals={len(rows)} successes={rows.successes.sum()} errors={rows.errors.sum()} "
              f"steps={rows.total_steps.sum()} cap_hits={rows.max_steps_hit.sum()} "
              f"tokens={rows.total_tokens.sum()} cost=${rows.total_cost.sum():.2f}")
