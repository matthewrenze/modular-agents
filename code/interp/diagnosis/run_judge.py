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
from interp.diagnosis.bundles import JudgeBundleRenderer
from interp.diagnosis.record import ExtendedRecordParser, FORMAT_REMINDER_EXTENDED

# Parameters
judge_names = ["gpt-5.6-sol", "claude-fable-5", "gemini-3.1-pro-preview"]
if os.environ.get("JUDGE"):
    judge_names = [os.environ["JUDGE"]]  # one process per provider = safe parallelism
conditions = ["pure", "feedback"]
if os.environ.get("CONDITION"):
    conditions = [os.environ["CONDITION"]]
failures_path = "../data/interp/failures.csv"
exclusions_path = "../data/interp/diagnosis/exclusions.csv"
output_folder = "../data/interp/diagnosis/judge"
limit_per_agent = None  # 5 = first-10 checkpoint (5 per architecture); None = full sweep

# Prompt versions are per condition: D1 = frozen pure/feedback (protocol section 7); D2 = the
# additive evolution condition (decisions section 99) — same taxonomy/instructions, bundle adds
# per-step plan/memory snapshots (modular only; react has no evolution to add)
PROMPT_VERSIONS = {"pure": "D1", "feedback": "D1", "evolution": "D2"}

PROMPT_HEAD_MODULAR_PURE = """You are a failure diagnostician auditing an LLM agent that played a text-based game (TextWorld) and FAILED its task. You see ONLY what the agent itself wrote during the episode: its final plan, its final memories, and its per-step summaries, thoughts, and actions. You do NOT see the game's responses, the game state, or the correct solution.

"""

PROMPT_HEAD_MODULAR_EVOLUTION = """You are a failure diagnostician auditing an LLM agent that played a text-based game (TextWorld) and FAILED its task. You see ONLY what the agent itself wrote during the episode: its per-step summaries, thoughts, and actions, its plan and its memories as they evolved during the episode (each shown at the steps where it changed), and its final plan and final memories. You do NOT see the game's responses, the game state, or the correct solution.

"""

PROMPT_HEAD_REACT_PURE = """You are a failure diagnostician auditing an LLM agent that played a text-based game (TextWorld) and FAILED its task. You see ONLY what the agent itself wrote during the episode: its per-step thoughts and actions. You do NOT see the game's responses, the game state, or the correct solution.

"""

PROMPT_HEAD_MODULAR_FEEDBACK = """You are a failure diagnostician auditing an LLM agent that played a text-based game (TextWorld) and FAILED its task. You see what the agent itself wrote during the episode — its final plan, its final memories, and its per-step summaries, thoughts, and actions — plus the game's per-step feedback text. You do NOT see the rest of the game state or the correct solution.

"""

PROMPT_HEAD_REACT_FEEDBACK = """You are a failure diagnostician auditing an LLM agent that played a text-based game (TextWorld) and FAILED its task. You see what the agent itself wrote during the episode — its per-step thoughts and actions — plus the game's per-step feedback text. You do NOT see the rest of the game state or the correct solution.

"""

PROMPT_HEADS = {("modular-full", "pure"): PROMPT_HEAD_MODULAR_PURE,
                ("react-kn", "pure"): PROMPT_HEAD_REACT_PURE,
                ("modular-full", "feedback"): PROMPT_HEAD_MODULAR_FEEDBACK,
                ("react-kn", "feedback"): PROMPT_HEAD_REACT_FEEDBACK,
                ("modular-full", "evolution"): PROMPT_HEAD_MODULAR_EVOLUTION}

PROMPT_TAIL_TOP = """

From this record alone, diagnose the primary cause of the failure.

Instructions:
- Read the entire record before concluding.
- The primary cause is the single most decisive reason this episode failed — the thing that, had it gone right, would most likely have flipped the outcome. Hitting the step limit is an outcome, not automatically a cause: ask WHY the agent did not finish in time.
- Choose `primary_cause` from this fixed taxonomy (use the slug exactly):
  - position-miscount-skip — Miscounted its position in the prescribed sequence (e.g. off-by-one, or conflating step count with move count) and executed a later instruction early, skipping one that was never performed
  - extra-move-insertion — Inserted a move the route does not contain — re-executing the just-completed instruction or extending a repeated run of identical moves by one
  - direction-misread — At the correct sequence position, misread the next instruction's direction and executed a different, substituted direction not in the route
  - lost-place-reanchor — Lost its place in the route text and re-anchored on a similar phrase elsewhere, jumping forward or rewinding to replay a block of instructions
  - route-copy-corruption — The agent's stored copy of the route was corrupted — instructions dropped, duplicated, or altered during transcription, replanning, or updates — and the agent faithfully executed the corrupted copy
  - checklist-overtick-skip — The agent's progress tracking marked route items as done that were never executed, so the following move(s) were skipped
  - intent-action-mismatch — The agent's stated intended move and its emitted command differ; the executed action contradicts the reasoning that chose it
  - cooking-recipe-errors — Recipe execution errors: misordered steps, wrong appliance, wrong cut, or misremembered recipe details
  - capacity-misbelief-loop — Falsely assumed an inventory-capacity limit blocked progress, causing futile item swapping or perceived deadlock
  - failed-move-desync — Advanced or failed to advance the route pointer correctly after failed or blocked movement attempts
  - hallucinated-state-quit — Hallucinated completion, success, or execution that never happened, causing premature quitting or skipped instructions
  - malformed-action-output — The agent emitted malformed output — meta-text, JSON, corrupted or duplicated command strings — instead of valid commands
  - abandoned-prescribed-route — Abandoned, truncated, or prematurely declared the prescribed route complete, often switching to exploration
  - other — Escape class: no listed class fits (also holds genuine one-off causes)
- Pick `other` only if no listed class fits. If two classes fit, the more specific one is `primary_cause` and the broader one is `secondary_cause`; otherwise `secondary_cause` is a second contributing slug or null.
- `root_cause_step`: the first step number at which the record shows the agent deviating from a path that could still have succeeded — for a specific slip, the step of the slip; for gradual drift, the first step where the agent is observably off the correct path. Use null ONLY if the failure cannot be tied to any step.
"""

FAULTY_MODULE_BULLET_MODULAR = "- `faulty_module`: the module that committed the root-cause error — `summarizer`, `memorizer`, `planner`, `reasoner`, or `actor`. Attribute the module that ORIGINATED the error, not the modules that propagated it. Use null only if no single module can be identified."

FAULTY_MODULE_BULLET_REACT = "- `faulty_module`: always null — this agent has no module decomposition."

PROMPT_TAIL_BOTTOM = """
- `confidence`: your subjective probability, 0.0–1.0, that your `primary_cause` is correct.
- `corrective_action`: one line — the single concrete change at the root-cause step that would most likely have flipped the outcome (for example, the exact command that should have been executed).
- Cite evidence as specific step numbers with a few words on what each shows.

Respond with ONLY a JSON object in this exact form:
{ "primary_cause": "<slug>", "secondary_cause": "<slug or null>",
  "root_cause_step": <integer or null>, "faulty_module": "<module or null>",
  "confidence": <0.0-1.0>, "corrective_action": "<one line>",
  "rationale": "<2-5 sentences>", "evidence": ["step N: <what it shows>", "..."] }"""

PROMPT_TAIL_MODULAR = PROMPT_TAIL_TOP + FAULTY_MODULE_BULLET_MODULAR + PROMPT_TAIL_BOTTOM
PROMPT_TAIL_REACT = PROMPT_TAIL_TOP + FAULTY_MODULE_BULLET_REACT + PROMPT_TAIL_BOTTOM

# Create the readers, renderer, and parser
artifacts = Artifacts()
episode_reader = EpisodeReader(artifacts, StateReader())
renderer = JudgeBundleRenderer()
parser = ExtendedRecordParser()
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
print(f"Episodes to judge: {len(failures)} x {len(judge_names)} judges x {len(conditions)} conditions", flush=True)

# Judge every episode with every judge under every condition, skipping already-persisted keys
grand_total_cost = 0.0
for judge_name in judge_names:
    model = ModelFactory().create(Parameters(model_name=judge_name), use_azure=False)
    if judge_name.startswith("claude"):
        model.max_tokens = 32768  # Claude thinking models spend thinking inside max_tokens; 16384 still truncated on ~40k-token bundles (both call and re-ask emitted zero text)
    judge_cost = 0.0
    for condition in conditions:
        role_folder = f"{output_folder}/{condition}/{judge_name}"
        os.makedirs(role_folder, exist_ok=True)
        for row in failures.to_dict("records"):
            is_modular = row["agent_name"] == "modular-full"
            if condition == "evolution" and not is_modular:
                continue  # react has no plan/memory evolution to add; its D1 bundles already carry its full output
            key = f"{row['model_name']}--{row['agent_name']}--{row['eval_name']}--episode-{row['episode']}"
            output_path = f"{role_folder}/{key}.json"
            if os.path.exists(output_path):
                # Skip only records from the current prompt version (stale versions are re-judged)
                with open(output_path, "r", encoding="utf-8") as f:
                    existing_version = json.load(f)["prompt_version"]
                if existing_version == PROMPT_VERSIONS[condition]:
                    print(f"Skipping {judge_name} / {condition} / {key} (already judged)", flush=True)
                    continue

            # Read the episode and render the artifact-only judge bundle (A2 caps; no solution, no env)
            params = Parameters(version=row["version"], split_name=row["split_name"], model_name=row["model_name"],
                                agent_name=row["agent_name"], eval_name=row["eval_name"], episode_id=int(row["episode"]))
            extract = episode_reader.read(params)
            bundle = renderer.render(extract, include_feedback=(condition == "feedback"),
                                     include_evolution=(condition == "evolution"))
            prompt_head = PROMPT_HEADS[(row["agent_name"], condition)]
            prompt_tail = PROMPT_TAIL_MODULAR if is_modular else PROMPT_TAIL_REACT
            prompt = prompt_head + bundle + prompt_tail

            # Get the judge's response (one re-ask on malformed JSON, per protocol section 3)
            start_time = time.time()
            model.reset_step()
            messages = [{"role": "user", "content": prompt}]
            response = model.get_response(messages)
            record = parser.parse(response)
            retry_response = None
            if record is None:
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": FORMAT_REMINDER_EXTENDED})
                retry_response = model.get_response(messages)
                record = parser.parse(retry_response)
            if record is not None and not is_modular:
                record["faulty_module"] = None  # forced for react (decisions section 69)
            elapsed = time.time() - start_time

            # Persist the parsed record, raw response(s), token counts, and cost
            cost = (cost_calculator.get_input_cost(judge_name, model.step_cached_tokens, model.step_input_tokens)
                    + cost_calculator.get_output_cost(judge_name, model.step_reasoning_tokens, model.step_output_tokens))
            judge_cost += cost
            output = {"judge": judge_name, "condition": condition, "model_version": model.model_version,
                      "prompt_version": PROMPT_VERSIONS[condition],
                      "version": row["version"], "split_name": row["split_name"], "model_name": row["model_name"],
                      "agent_name": row["agent_name"], "eval_name": row["eval_name"], "episode": int(row["episode"]),
                      "record": record, "bundle_chars": len(bundle), "prompt_chars": len(prompt),
                      "tokens": {"cached": model.step_cached_tokens, "input": model.step_input_tokens,
                                 "reasoning": model.step_reasoning_tokens, "output": model.step_output_tokens,
                                 "total": model.step_total_tokens},
                      "cost": round(cost, 4), "elapsed_seconds": round(elapsed, 1),
                      "raw_response": response, "raw_retry_response": retry_response}
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2)
            cause = record["primary_cause"] if record else "MALFORMED"
            print(f"Judged {judge_name} / {condition} / {key}: cause = {cause} | "
                  f"input tokens = {model.step_cached_tokens + model.step_input_tokens}, "
                  f"output tokens = {model.step_reasoning_tokens + model.step_output_tokens}, "
                  f"cost = ${cost:.3f}, time = {elapsed:.0f}s", flush=True)
    grand_total_cost += judge_cost
    print(f"Judge {judge_name} cost: ${judge_cost:.2f}", flush=True)

print(f"Total cost: ${grand_total_cost:.2f}")
