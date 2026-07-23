import json
import os
import time
import pandas as pd
from artifacts.artifacts import Artifacts
from models.cost_calculator import CostCalculator
from models.model_factory import ModelFactory
from params.parameters import Parameters
from states.reader.state_reader import StateReader
from interp.episode_reader import EpisodeReader
from interp.diagnosis.agentic import ActionParser, RetrievalTools, AgenticSession, build_intro

# Parameters
judge_names = ["gpt-5.6-sol", "claude-fable-5", "gemini-3.1-pro-preview"]
if os.environ.get("JUDGE"):
    judge_names = [os.environ["JUDGE"]]  # one process per provider = safe parallelism
failures_path = "../data/interp/failures.csv"
exclusions_path = "../data/interp/diagnosis/exclusions.csv"
output_folder = "../data/interp/diagnosis/agentic-judge"
limit_per_agent = None  # 5 = first-10 checkpoint (5 per architecture); None = full sweep

PROMPT_VERSION = "E1"  # verbatim E1 prompt text lives in agentic.py (build_intro and its constants)

def main():
    # Create the readers and parser
    artifacts = Artifacts()
    episode_reader = EpisodeReader(artifacts, StateReader())
    parser = ActionParser()
    cost_calculator = CostCalculator()

    # Select the scored population: the pre-registered failures minus the Gate 3 exclusions
    failures = pd.read_csv(failures_path)
    exclusions = pd.read_csv(exclusions_path)
    merged = failures.merge(exclusions[["model_name", "agent_name", "eval_name", "episode"]],
                            on=["model_name", "agent_name", "eval_name", "episode"], how="left", indicator=True)
    failures = failures[(merged["_merge"] == "left_only").values]
    if limit_per_agent is not None:
        failures = failures.groupby("agent_name", sort=False).head(limit_per_agent)
    if os.environ.get("SHARD"):
        shard, n_shards = (int(x) for x in os.environ["SHARD"].split("/"))
        failures = failures.iloc[shard::n_shards]  # disjoint slices per process; per-episode skip logic remains the safety net
    print(f"Episodes to judge: {len(failures)} x {len(judge_names)} judges (agentic)", flush=True)

    # Judge every episode with every judge, skipping already-persisted keys
    grand_total_cost = 0.0
    for judge_name in judge_names:
        model = ModelFactory().create(Parameters(model_name=judge_name), use_azure=False)
        if judge_name.startswith("claude"):
            model.max_tokens = 32768  # Claude thinking models spend thinking inside max_tokens (decisions sections 71/89)
            model.timeout = 1200.0  # silent stalls burn the full timeout; legit agentic calls finish in < 8 min
        judge_cost = 0.0
        role_folder = f"{output_folder}/{judge_name}"
        os.makedirs(role_folder, exist_ok=True)
        for row in failures.to_dict("records"):
            is_modular = row["agent_name"] == "modular-full"
            key = f"{row['model_name']}--{row['agent_name']}--{row['eval_name']}--episode-{row['episode']}"
            output_path = f"{role_folder}/{key}.json"
            if os.path.exists(output_path):
                # Skip only records from the current prompt version (stale versions are re-judged)
                with open(output_path, "r", encoding="utf-8") as f:
                    existing_version = json.load(f)["prompt_version"]
                if existing_version == PROMPT_VERSION:
                    print(f"Skipping {judge_name} / {key} (already judged)", flush=True)
                    continue

            # Read the episode and run the metered read-and-diagnose session
            params = Parameters(version=row["version"], split_name=row["split_name"], model_name=row["model_name"],
                                agent_name=row["agent_name"], eval_name=row["eval_name"], episode_id=int(row["episode"]))
            extract = episode_reader.read(params)
            tools = RetrievalTools(extract, is_modular)
            intro = build_intro(extract.state.task_state.task, len(extract.details), is_modular)
            start_time = time.time()
            session = AgenticSession(model, tools, parser, intro)
            result = session.run()
            record = result["record"]
            if record is not None and not is_modular:
                record["faulty_module"] = None  # forced for react (decisions section 69)
            elapsed = time.time() - start_time

            # Persist the parsed record, retrieval accounting, per-turn tokens, transcript, and cost
            tokens = {name: sum(turn[name] for turn in result["turn_tokens"])
                      for name in ("cached", "input", "reasoning", "output")}
            tokens["total"] = sum(tokens.values())
            cost = (cost_calculator.get_input_cost(judge_name, tokens["cached"], tokens["input"])
                    + cost_calculator.get_output_cost(judge_name, tokens["reasoning"], tokens["output"]))
            judge_cost += cost
            output = {"judge": judge_name, "condition": "agentic", "model_version": model.model_version,
                      "prompt_version": PROMPT_VERSION,
                      "version": row["version"], "split_name": row["split_name"], "model_name": row["model_name"],
                      "agent_name": row["agent_name"], "eval_name": row["eval_name"], "episode": int(row["episode"]),
                      "record": record, "outcome": result["outcome"],
                      "read_turns": result["read_turns"], "n_turns": result["n_turns"],
                      "retrieval": {"total_chars": tools.total_chars, "channel_chars": tools.channel_chars,
                                    "calls": tools.calls},
                      "intro_chars": len(intro), "tokens": tokens, "turn_tokens": result["turn_tokens"],
                      "cost": round(cost, 4), "elapsed_seconds": round(elapsed, 1),
                      "transcript": result["messages"]}
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2)
            cause = record["primary_cause"] if record else result["outcome"].upper()
            print(f"Judged {judge_name} / {key}: cause = {cause} | reads = {result['read_turns']} turns / "
                  f"{tools.total_chars} chars retrieved | input tokens = {tokens['cached'] + tokens['input']}, "
                  f"output tokens = {tokens['reasoning'] + tokens['output']}, "
                  f"cost = ${cost:.3f}, time = {elapsed:.0f}s", flush=True)
        grand_total_cost += judge_cost
        print(f"Judge {judge_name} cost: ${judge_cost:.2f}", flush=True)

    print(f"Total cost: ${grand_total_cost:.2f}")

if __name__ == "__main__":
    main()  # import-safe: importing this module must never start a billable sweep
