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
from interp.plan.solution_reader import SolutionReader
from interp.diagnosis.bundles import LabelerBundleRenderer
from interp.diagnosis.record import RecordParser, FORMAT_REMINDER

# Parameters
labeler_name = "gpt-5.6-sol"
failures_path = "../data/interp/failures.csv"
output_folder = "../data/interp/diagnosis/pre-labeler"
limit_per_agent = None  # 5 = first-10 checkpoint (5 per architecture); None = full sweep

PROMPT_VERSION = "A2"  # A1 = uncapped bundles (first-10 checkpoint, archived); A2 = size caps (decisions section 62)

PROMPT_HEAD = """You are a failure analyst for LLM agents that play text-based games (TextWorld). You will receive the complete record of ONE episode in which the agent FAILED its task, together with the task's ground-truth solution. Your job is to determine the primary cause of the failure.

"""

PROMPT_TAIL = """

Instructions:
- Read the entire record before concluding.
- The primary cause is the single most decisive reason this episode failed — the thing that, had it gone right, would most likely have flipped the outcome.
- Hitting the step limit is an outcome, not automatically a cause: ask WHY the agent did not finish in time. Cite running out of steps as the cause only if the agent was making steady, correct progress and simply had too few steps.
- Name the cause in your own words as a short phrase (at most 8 words), specific enough that another analyst reading this record would recognize it.
- Optionally name a distinct secondary cause that also contributed.
- Cite evidence as specific step numbers with a few words on what each shows.

Respond with ONLY a JSON object in this exact form:
{ "primary_cause": "<short phrase>", "secondary_cause": "<short phrase or null>",
  "rationale": "<2-5 sentences>", "evidence": ["step N: <what it shows>", "..."] }"""

# Create the readers, renderer, parser, and model
artifacts = Artifacts()
episode_reader = EpisodeReader(artifacts, StateReader())
solution_reader = SolutionReader()
renderer = LabelerBundleRenderer()
parser = RecordParser()
model = ModelFactory().create(Parameters(model_name=labeler_name), use_azure=False)
cost_calculator = CostCalculator()

# Select the failure episodes to label (the pre-registered population, in stored order)
failures = pd.read_csv(failures_path)
if limit_per_agent is not None:
    failures = failures.groupby("agent_name", sort=False).head(limit_per_agent)
print(f"Episodes to label: {len(failures)}", flush=True)

# Label every episode, skipping already-persisted keys (every sweep is resumable)
role_folder = f"{output_folder}/{labeler_name}"
os.makedirs(role_folder, exist_ok=True)
total_cost = 0.0
for row in failures.to_dict("records"):
    key = f"{row['model_name']}--{row['agent_name']}--{row['eval_name']}--episode-{row['episode']}"
    output_path = f"{role_folder}/{key}.json"
    if os.path.exists(output_path):
        # Skip only records from the current prompt version (stale versions are re-labeled)
        with open(output_path, "r", encoding="utf-8") as f:
            existing_version = json.load(f)["prompt_version"]
        if existing_version == PROMPT_VERSION:
            print(f"Skipping {key} (already labeled)", flush=True)
            continue

    # Read the episode and render the labeler bundle
    params = Parameters(version=row["version"], split_name=row["split_name"], model_name=row["model_name"],
                        agent_name=row["agent_name"], eval_name=row["eval_name"], episode_id=int(row["episode"]))
    extract = episode_reader.read(params)
    solution = solution_reader.read(row["split_name"], row["eval_name"], int(row["episode"]))
    bundle = renderer.render(extract, solution, row)
    prompt = PROMPT_HEAD + bundle + PROMPT_TAIL

    # Get the labeler's response (one re-ask on malformed JSON, per protocol section 3)
    start_time = time.time()
    model.reset_step()
    messages = [{"role": "user", "content": prompt}]
    response = model.get_response(messages)
    record = parser.parse(response)
    retry_response = None
    if record is None:
        messages.append({"role": "assistant", "content": response})
        messages.append({"role": "user", "content": FORMAT_REMINDER})
        retry_response = model.get_response(messages)
        record = parser.parse(retry_response)
    elapsed = time.time() - start_time

    # Persist the parsed record, raw response(s), token counts, and cost
    cost = (cost_calculator.get_input_cost(labeler_name, model.step_cached_tokens, model.step_input_tokens)
            + cost_calculator.get_output_cost(labeler_name, model.step_reasoning_tokens, model.step_output_tokens))
    total_cost += cost
    output = {"labeler": labeler_name, "model_version": model.model_version, "prompt_version": PROMPT_VERSION,
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
    print(f"Labeled {key}: cause = {cause} | input tokens = {model.step_cached_tokens + model.step_input_tokens}, "
          f"output tokens = {model.step_reasoning_tokens + model.step_output_tokens}, "
          f"cost = ${cost:.3f}, time = {elapsed:.0f}s", flush=True)

print(f"Total cost: ${total_cost:.2f}")
