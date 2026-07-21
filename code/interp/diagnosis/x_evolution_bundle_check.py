import json
import pandas as pd
from artifacts.artifacts import Artifacts
from states.reader.state_reader import StateReader
from interp.episode_reader import EpisodeReader
from interp.diagnosis.bundles import JudgeBundleRenderer
from params.parameters import Parameters

# Scratch: pre-sweep sanity for the D2 evolution condition (decisions section 99).
# 1) Regression guard: pure bundles must be byte-identical in size to the persisted D1 records.
# 2) Size report: evolution bundle chars vs pure, for the cost forecast.

failures = pd.read_csv("../data/interp/failures.csv")
exclusions = pd.read_csv("../data/interp/diagnosis/exclusions.csv")
merged = failures.merge(exclusions[["model_name", "agent_name", "eval_name", "episode"]],
                        on=["model_name", "agent_name", "eval_name", "episode"], how="left", indicator=True)
failures = failures[(merged["_merge"] == "left_only").values]
modular = failures[failures.agent_name == "modular-full"]
print(f"Modular scored episodes: {len(modular)}")

episode_reader = EpisodeReader(Artifacts(), StateReader())
renderer = JudgeBundleRenderer()
mismatches, rows = 0, []
for row in modular.to_dict("records"):
    params = Parameters(version=row["version"], split_name=row["split_name"], model_name=row["model_name"],
                        agent_name=row["agent_name"], eval_name=row["eval_name"], episode_id=int(row["episode"]))
    extract = episode_reader.read(params)
    pure = renderer.render(extract)
    evolution = renderer.render(extract, include_evolution=True)
    key = f"{row['model_name']}--{row['agent_name']}--{row['eval_name']}--episode-{row['episode']}"
    with open(f"../data/interp/diagnosis/judge/pure/gpt-5.6-sol/{key}.json", "r", encoding="utf-8") as f:
        persisted = json.load(f)["bundle_chars"]
    if len(pure) != persisted:
        mismatches += 1
        print(f"PURE MISMATCH {key}: now {len(pure)} vs persisted {persisted}")
    rows.append({"key": key, "pure_chars": len(pure), "evolution_chars": len(evolution)})

report = pd.DataFrame(rows)
report.to_csv("../data/interp/diagnosis/evolution-bundle-sizes.csv", index=False)
print(f"Pure-bundle regressions: {mismatches}")
print(f"Pure chars:      mean {report.pure_chars.mean():,.0f}, max {report.pure_chars.max():,}")
print(f"Evolution chars: mean {report.evolution_chars.mean():,.0f}, max {report.evolution_chars.max():,}")
print(f"Mean growth: x{(report.evolution_chars / report.pure_chars).mean():.2f}")
