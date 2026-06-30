# Import packages
from logs.console import warn
from params.parameters_factory import ParametersFactory
from evals.eval_factory import EvalFactory
from results.results_manager import ResultsManager
from summaries.summary_manager import SummaryManager
from run_episode import run_episode

# Set train/test split
split_name = "train"

# Set models
model_names = [
    # "claude-sonnet-4-6",
    # "deepseek-v4-pro",
    # "gemini-3.1-pro-preview",
    # "gpt-5.2",
    # "gpt-5.4-mini",
    "gpt-5.4",
    # "gpt-5.5",
    # "glm-5-fast"
    # "glm-5.1",
    # "kimi-k2.5-turbo",
    # "kimi-k2.6",
    # "qwen3.6-plus",
]

# Set agents
agent_names = [
    # "react-k0-v6.0",
    # "react-k1-v6.0",
    # "react-kn-v6.0",
    # "modular-base-v6.0",
    # "plus-planner-v6.0",
    # "plus-summarizer-v6.0",
    # "plus-memorizer-v6.0",
    # "minus-planner-v6.0",
    # "minus-summarizer-v6.0",
    # "minus-memorizer-v6.0",
    "modular-full-v6.0"
]
# Set evals
eval_size = 1
eval_env_names = [
    # ("tw-quick-1", "textworld"),
    # # #
    ("tw-simple-1", "textworld"),
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

# Create components
eval_factory = EvalFactory()

for params in runs:
    print(f"--- Running {params.split_name} - {params.model_name} - {params.agent_name} - {params.eval_name} ---")

    # Create components
    results_manager = ResultsManager()
    summary_manager = SummaryManager()

    # Create the eval
    eval = eval_factory.create(params)

    # Get the episodes to run
    num_episodes = min(len(eval), eval_size)
    episode_ids = list(range(1, num_episodes + 1))
    # HACK: select specific episodes for specific num_episodes
    if num_episodes == 1:
        episode_ids = [1]
    if num_episodes == 10:
        episode_ids = list(range(10, 101, 10))
    if num_episodes == 99:
        episode_ids = [100]

    # Set up summaries
    if summary_manager.exists(params):
        warn(f"Summary for {params.split_name} - {params.model_name} - {params.agent_name} - {params.eval_name} already exists.")
        input("Press Enter to continue...")

    # Run the episodes
    for episode_id in episode_ids:
        run_episode(
            split_name=params.split_name,
            model_name=params.model_name,
            agent_name=params.agent_name,
            env_name=params.env_name,
            eval_name=params.eval_name,
            episode_id=episode_id)

    # Load the results for the summary
    results_manager.load(params)

    # Save the summary
    results = results_manager.get_table()
    results["error"] = results["error"].fillna("")
    summary = summary_manager.summarize(results)
    summary_manager.append(summary)

    # Display the summaries
    print(f"Total Episodes: {summary.episodes}")
    print(f"Accuracy: {summary.accuracy:.0%}")
    print(f"Correct Tasks: {summary.successes}")
    print(f"Failed Tasks: {summary.failures}")
    print(f"Errors: {summary.errors}")
    print(f"Total Tokens: {summary.total_tokens}")
    print(f"Total Cost: ${summary.total_cost:.2f}")
    print(f"Total Time: {summary.total_time:.2f} seconds")
    print(f"Avg Reward per Episode: {summary.avg_reward_per_episode:.2f}")
    print(f"Avg Reward per Step: {summary.avg_reward_per_step:.4f}")
    print(f"Avg Reward per Token: {summary.avg_reward_per_token:.6f}")
    print("--- END OF EVAL ---" )
    print("")
