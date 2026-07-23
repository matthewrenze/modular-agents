# Scratch: free pre-sweep check for the agentic judge (E1). For every scored episode, build the
# retrieval tools and intro prompt (verifies clean construction on real data) and record the
# full-read size of every channel — the exhaustive-read upper bound for the cost forecast.
# Output: data/interp/diagnosis/agentic-channel-sizes.csv
import pandas as pd
from artifacts.artifacts import Artifacts
from params.parameters import Parameters
from states.reader.state_reader import StateReader
from interp.episode_reader import EpisodeReader
from interp.diagnosis.agentic import RetrievalTools, MODULAR_TOOLS, REACT_TOOLS, build_intro

failures = pd.read_csv("../data/interp/failures.csv")
exclusions = pd.read_csv("../data/interp/diagnosis/exclusions.csv")
merged = failures.merge(exclusions[["model_name", "agent_name", "eval_name", "episode"]],
                        on=["model_name", "agent_name", "eval_name", "episode"], how="left", indicator=True)
failures = failures[(merged["_merge"] == "left_only").values]
print(f"Episodes: {len(failures)}")

episode_reader = EpisodeReader(Artifacts(), StateReader())
rows = []
for row in failures.to_dict("records"):
    params = Parameters(version=row["version"], split_name=row["split_name"], model_name=row["model_name"],
                        agent_name=row["agent_name"], eval_name=row["eval_name"], episode_id=int(row["episode"]))
    extract = episode_reader.read(params)
    is_modular = row["agent_name"] == "modular-full"
    tools = RetrievalTools(extract, is_modular)
    intro = build_intro(extract.state.task_state.task, len(extract.details), is_modular)
    sizes = {tool: len(tools.execute(tool)) for tool in (MODULAR_TOOLS if is_modular else REACT_TOOLS)}
    rows.append({"model_name": row["model_name"], "agent_name": row["agent_name"],
                 "eval_name": row["eval_name"], "episode": int(row["episode"]),
                 "n_steps": len(extract.details), "intro_chars": len(intro),
                 "exhaustive_chars": tools.total_chars, **sizes})

frame = pd.DataFrame(rows)
frame.to_csv("../data/interp/diagnosis/agentic-channel-sizes.csv", index=False)
print(frame.groupby("agent_name")[["intro_chars", "exhaustive_chars"]].describe().round(0).to_string())
tool_columns = [column for column in frame.columns if column.startswith("read_")]
print("\nMean full-read chars per tool by architecture:")
print(frame.groupby("agent_name")[tool_columns].mean().round(0).to_string())
