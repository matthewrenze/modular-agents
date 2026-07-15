# Import packages
from episodes.episode import Episode

# Set train/test split
split_name = "train"

# Set models
model_names = [
    # "claude-sonnet-4-6",
    # "gemini-3.1-pro-preview",
    # "gpt-5.2",
    # "gpt-5.4",
    # "gpt-5.5",
    # "kimi-k2.7-code",
    # "glm-5.2",
    # "minimax-m3",
    # "deepseek-v4-pro",
    # "nemotron-3-ultra",
]

# Set agents
agent_names = [
    # "react-k0",
    # "react-k1",
    # "react-kn",
    # "modular-base",
    # "plus-planner",
    # "plus-summarizer",
    # "plus-memorizer",
    # "minus-planner",
    # "minus-summarizer",
    # "minus-memorizer",
    # "modular-full"
]
# Set evals
eval_size = 10
eval_env_names = [
    # ("tw-quick-1", "textworld"),
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

# Select the episodes to run
if eval_size == 1:
    episode_ids = [1]
elif eval_size == 10:
    episode_ids = list(range(10, 101, 10))
elif eval_size == 99:
    episode_ids = [100]
else:
    episode_ids = list(range(1, eval_size + 1))

# Run each combo's episodes sequentially (parallelism is by running this in multiple windows)
episode = Episode()
counts = {"success": 0, "failure": 0, "error": 0, "skipped": 0}
for model_name in model_names:
    for agent_name in agent_names:
        for eval_name, env_name in eval_env_names:
            for episode_id in episode_ids:
                status = episode.run(
                    split_name=split_name,
                    model_name=model_name,
                    agent_name=agent_name,
                    env_name=env_name,
                    eval_name=eval_name,
                    episode_id=episode_id)
                counts[status] += 1

# Report the run tally
print(f"Total Episodes: {sum(counts.values())}")
print(f"Succeeded:      {counts['success']}")
print(f"Failed:         {counts['failure']}")
print(f"Errored:        {counts['error']}")
print(f"Skipped:        {counts['skipped']}")
