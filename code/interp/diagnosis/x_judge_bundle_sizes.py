import pandas as pd
from artifacts.artifacts import Artifacts
from params.parameters import Parameters
from states.reader.state_reader import StateReader
from interp.episode_reader import EpisodeReader
from interp.diagnosis.bundles import JudgeBundleRenderer

CHARS_PER_TOKEN = 3.25  # measured on gpt-5.6-sol at the Phase A checkpoint (decisions section 59)

failures = pd.read_csv("../data/interp/failures.csv")
exclusions = pd.read_csv("../data/interp/diagnosis/exclusions.csv")
merged = failures.merge(exclusions[["model_name", "agent_name", "eval_name", "episode"]],
                        on=["model_name", "agent_name", "eval_name", "episode"], how="left", indicator=True)
failures = failures[(merged["_merge"] == "left_only").values]

episode_reader = EpisodeReader(Artifacts(), StateReader())
renderer = JudgeBundleRenderer()
rows = []
for row in failures.to_dict("records"):
    params = Parameters(version=row["version"], split_name=row["split_name"], model_name=row["model_name"],
                        agent_name=row["agent_name"], eval_name=row["eval_name"], episode_id=int(row["episode"]))
    extract = episode_reader.read(params)
    pure = renderer.render(extract, include_feedback=False)
    feedback = renderer.render(extract, include_feedback=True)
    rows.append({"model_name": row["model_name"], "agent_name": row["agent_name"],
                 "eval_name": row["eval_name"], "episode": row["episode"],
                 "pure_chars": len(pure), "feedback_chars": len(feedback),
                 "pure_est_tokens": round(len(pure) / CHARS_PER_TOKEN),
                 "feedback_est_tokens": round(len(feedback) / CHARS_PER_TOKEN),
                 "truncated": "[... truncated" in pure})

sizes = pd.DataFrame(rows)
sizes.to_csv("../data/interp/diagnosis/judge-bundle-sizes.csv", index=False)
print(f"Episodes: {len(sizes)}")
print(sizes.groupby("agent_name")[["pure_est_tokens", "feedback_est_tokens"]].agg(["mean", "median", "max"]).round(0))
print(f"Total est input tokens (pure + feedback): {sizes.pure_est_tokens.sum() + sizes.feedback_est_tokens.sum():,}")
print(f"Truncated bundles: {sizes.truncated.sum()}")
