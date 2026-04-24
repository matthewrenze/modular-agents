from evals.eval_factory import EvalFactory
from logs.log_reader import LogReader
from messages.messages_writer import MessagesWriter
from models.model_factory import ModelFactory
from params.parameters_factory import ParametersFactory
from agents.agent_factory import AgentFactory
from agents.reviewer.reviewer import Reviewer
from results.results_manager import ResultsManager
from reviews.writer.review_writer import ReviewWriter
from typing import cast
from logs.console import warn

# Set provider
# FIXME: *** WARNING: THIS IS THE REVIEW SCRIPT ***
use_azure = False

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
    # "react-k0-v5.0",
    # "react-k1-v5.0",
    # "react-kn-v5.0",
    "modular-base-v5.0",
    # "plus-planner-v5.0",
    # "plus-summarizer-v5.0",
    # "plus-memorizer-v5.0",
    # "minus-planner-v5.0",
    # "minus-summarizer-v5.0",
    # "minus-memorizer-v5.0",
    # "modular-full-v5.0"
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

task_types_map = {
    "tw-quick": "prepare a meal",
    "tw-simple": "find and place an item",
    "tw-treasure": "find the hidden treasure",
    "tw-coin": "collect a gold coin",
    "tw-cooking": "prepare a meal"}

# Create the runs
runs = []
parameters_factory = ParametersFactory()
for model_name in model_names:
    for agent_name in agent_names:
        for eval_env_name in eval_env_names:
            eval_name, env_name = eval_env_name
            params = parameters_factory.create(
                split_name=split_name,
                model_name=model_name,
                agent_name = agent_name,
                env_name = env_name,
                eval_name = eval_name,
                eval_size = eval_size)
            runs.append(params)

for params in runs:
    print(f"--- Reviewing {params.split_name} - {params.model_name} - {params.agent_name} - {params.eval_name} - {eval_size} episodes ---")

    # Get the episode ids
    eval = EvalFactory().create(params)
    num_episodes = min(len(eval), eval_size)
    episode_ids = list(range(1, num_episodes + 1))
    if num_episodes == 10:
        episode_ids = list(range(10, 101, 10))

    # Load the results
    results_manager = ResultsManager()
    results_manager.load(params)
    results = results_manager.get_table()

    for episode_id in episode_ids:

        print(f"--- Reviewing {params.split_name} - {params.model_name} - {params.agent_name} - {params.eval_name} - episode-{episode_id} ---")

        try:

            # Read the log file for the episode
            log_reader = LogReader()
            log_text = log_reader.read(params, episode_id)
            log_lines = log_text.splitlines()
            log_text = "\n".join(log_lines[2:-1])

            # Load the eval
            episode = eval.iloc[episode_id - 1].to_dict()
            task = episode["task"]
            solution_steps = episode["solution_steps"]
            solution = episode["solution"]

            # Get the result
            result = results[results["episode"] == episode_id].iloc[0]
            reward = result["reward"]
            score = result["score"]
            max_score = result["max_score"]
            steps = result["steps"]
            max_steps = result["max_steps"]

            # Create the review header
            header = f"Agent: {params.agent_name}\n"
            header += f"Split: {params.split_name}\n"
            header += f"Model: {params.model_name}\n"
            header += f"Eval: {params.eval_name}\n"
            header += f"Task: {task_types_map.get(params.eval_name.rsplit("-", 1)[0], '')}\n"
            header += f"Outcome: {'success' if reward == 1.0 else 'failure'}\n"
            header += f"Score: {score} of {max_score} points\n"
            header += f"Duration: {steps} of {max_steps} steps\n"

            # Review the episode
            model = ModelFactory().create(params, use_azure)
            reviewer = AgentFactory().create("reviewer", params, model)
            reviewer = cast(Reviewer, reviewer)
            review = reviewer.review(task, solution, solution_steps, log_text)

            # Write the reviewer's messages
            messages_writer = MessagesWriter()
            messages_writer.write(params, episode_id, 1, "reviewer", reviewer.messages)

            # Add the header
            review = header + review

            # Write the review
            review_writer = ReviewWriter()
            review_writer.write(params, episode_id, review)

            # Print the review
            # print(review)

        except Exception as e:
            warn(f"Error creating review: {str(e)}")