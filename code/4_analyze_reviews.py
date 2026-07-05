import regex as re
from artifacts.artifacts import Artifacts
from evals.eval_factory import EvalFactory
from models.model_factory import ModelFactory
from params.parameters_factory import ParametersFactory
from agents.agent_factory import AgentFactory
from agents.analyzer.analyzer import Analyzer
from reviews.reader.review_reader import ReviewReader
from reviews.analysis.analysis_writer import AnalysisWriter
from typing import cast
from logs.console import warn

# Set provider
# FIXME: *** WARNING: THIS IS THE REVIEW SCRIPT ***
use_azure = False

# Set version
# FIXME: *** WARNING: THIS IS THE REVIEW SCRIPT ***
version = "v6.0"

# Set train/test split
# FIXME: *** WARNING: THIS IS THE REVIEW SCRIPT ***
split_name = "train"

# Set models
# FIXME: *** WARNING: THIS IS THE REVIEW SCRIPT ***
model_names = [
    # "claude-sonnet-4-6",
    # "deepseek-v3.2"
    # "gemini-3.1-pro-preview",
    # "gpt-5.2",
    "gpt-5.4-mini",
    # "gpt-5.4",
    # "glm-5-fast"
    # "kimi-k2.5"
]

# Set agents
# FIXME: *** WARNING: THIS IS THE REVIEW SCRIPT ***
agent_names = [
    # "react-k0",
    # "react-k1",
    # "react-kn",
    "modular-base",
    # "plus-planner",
    # "plus-summarizer",
    # "plus-memorizer",
    # "minus-planner",
    # "minus-summarizer",
    # "minus-memorizer",
    # "modular-full"
]
# Set evals
# FIXME: *** WARNING: THIS IS THE REVIEW SCRIPT ***
eval_size = 10
eval_env_names = [
    ("tw-quick-1", "textworld"),
    # # #
    # ("tw-simple-1", "textworld"),
    # ("tw-treasure-1", "textworld"),
    # ("tw-treasure-2", "textworld"),
    # ("tw-treasure-3", "textworld"),
    # ("tw-coin-1", "textworld"),
    # ("tw-coin-2", "textworld"),
    # ("tw-coin-3", "textworld"),
    # ("tw-cooking-1", "textworld"),
    # ("tw-cooking-2", "textworld"),
    # ("tw-cooking-3", "textworld"),
]

# Create the runs
runs = []
artifacts = Artifacts()
parameters_factory = ParametersFactory()
for eval_env_name in eval_env_names:
    eval_name, env_name = eval_env_name
    params = parameters_factory.create(
        split_name=split_name,
        model_name=model_names[0],
        agent_name=agent_names[0],
        env_name=env_name,
        eval_name=eval_name,
        eval_size=eval_size)
    params.version = version
    runs.append(params)

print(f"--- Analyzing {model_names[0]} - {agent_names[0]}  ---")

# Create the review list
reviews = f"Model: {model_names[0]}\n"
reviews += f"Agent: {agent_names[0]}\n"
reviews += "---\n"

for params in runs:

    # Get the episode ids
    eval = EvalFactory().create(params)
    num_episodes = min(len(eval), eval_size)
    episode_ids = list(range(1, num_episodes + 1))
    if num_episodes == 10:
        episode_ids = list(range(10, 101, 10))

    for episode_id in episode_ids:

        params.episode_id = episode_id

        print(f"--- Reading {params.split_name} - {params.agent_name} - {params.model_name} - {params.eval_name} - episode-{episode_id} ---")

        try:

            # Read the review
            review_reader = ReviewReader(artifacts)
            review_text = review_reader.read(params)
            review_lines = review_text.splitlines()

            # Remove the first two lines (agent and model)
            review_lines = review_lines[3:]

            # Remove the steps-wise analysis from the review
            filtered_lines = []
            for i, line in enumerate(review_lines):
                if re.match(r"^Steps:", line):
                    continue
                if re.match(r"^  \d+:", line):
                    continue
                filtered_lines.append(line)

            # Join the filtered lines
            review_text = "\n".join(filtered_lines)

            # Add the review to the list
            reviews += f"Eval: {params.eval_name}\n"
            reviews += f"Episode: {episode_id}\n"
            reviews += review_text
            reviews += "\n---\n"

        except Exception as e:
            warn(f"Error reading review: {str(e)}")
            continue

# Analyze the reviews
print("Performing analysis of reviews...")
params = runs[0]
model = ModelFactory().create(params, use_azure)
analyzer = AgentFactory().create("analyzer", params, model)
analyzer = cast(Analyzer, analyzer)
analysis = analyzer.analyze(reviews)

# Write the analysis
analysis_writer = AnalysisWriter(artifacts)
analysis_writer.write(params, analysis)

# Print analysis
print("--- Analysis ---\n\n\n")
print(analysis)