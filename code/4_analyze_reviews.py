import regex as re
from evals.eval_factory import EvalFactory
from models.model_factory import ModelFactory
from params.parameters_factory import ParametersFactory
from agents.agent_factory import AgentFactory
from agents.analyzer.analyzer import Analyzer
from reviews.reader.review_reader import ReviewReader
from reviews.analysis.analysis_writer import AnalysisWriter
from typing import cast
from logs.console import warn

# Set models
# FIXME: *** WARNING: THIS IS THE REVIEW SCRIPT ***
model_names = [
    "gpt-5-mini",
    # "gpt-5.2"
]


# Set agents
# FIXME: *** WARNING: THIS IS THE REVIEW SCRIPT ***
agent_names = [
    # "react-k0",
    # "react-k1",
    # "react-kn",
    "baseline-v2",
    # "plus-tasker-v2",
    # "plus-planner-v2"
    # "plus-summarizer-v2",
    # "plus-memorizer-v2",
    # "plus-reasoner-v2",
    # "minus-tasker",
    # "minus-summarizer",
    # "minus-memorizer",
    # "minus-reasoner"
    # "topline-v2"
]

# Set evals
# FIXME: *** WARNING: THIS IS THE REVIEW SCRIPT ***
eval_size = 10
eval_env_names = [
    ("tw-simple-1", "textworld"),
    ("tw-treasure-1", "textworld"),
    ("tw-treasure-2", "textworld"),
    ("tw-treasure-3", "textworld"),
    ("tw-coin-1", "textworld"),
    ("tw-coin-2", "textworld"),
    ("tw-coin-3", "textworld"),
    ("tw-cooking-1", "textworld"),
    ("tw-cooking-2", "textworld"),
    ("tw-cooking-3", "textworld"),
]

# Create the runs
runs = []
parameters_factory = ParametersFactory()
for eval_env_name in eval_env_names:
    eval_name, env_name = eval_env_name
    params = parameters_factory.create(
        model_name=model_names[0],
        agent_name = agent_names[0],
        env_name = env_name,
        eval_name = eval_name,
        eval_size = eval_size)
    runs.append(params)

print(f"--- Analyzing {agent_names[0]} - {model_names[0]} ---")

# Create the review list
reviews = f"Agent: {agent_names[0]}\n"
reviews += f"Model: {model_names[0]}\n"
reviews += "---\n"

for params in runs:

    # Get the episode ids
    eval = EvalFactory().create(params)
    num_episodes = min(len(eval), eval_size)
    episode_ids = list(range(1, num_episodes + 1))
    if num_episodes == 10:
        episode_ids = list(range(10, 101, 10))

    for episode_id in episode_ids:

        print(f"--- Reading {params.agent_name} - {params.model_name} - {params.eval_name} - {episode_id} of {len(episode_ids)}---")

        try:

            # Read the review
            review_reader = ReviewReader()
            review_text = review_reader.read(params, episode_id)
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
model = ModelFactory().create(params)
analyzer = AgentFactory().create("analyzer", params, model)
analyzer = cast(Analyzer, analyzer)
analysis = analyzer.analyze(reviews)

# Write the analysis
analysis_writer = AnalysisWriter()
analysis_writer.write(params, analysis)

# Print analysis
print("--- Analysis ---\n\n\n")
print(analysis)