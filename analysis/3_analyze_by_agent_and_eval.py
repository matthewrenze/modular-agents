import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# Set parameters
version = "v6.0"
model_name = "gpt-5.4"
# model_name = "gpt-5.4-mini"
# model_name = "claude-sonnet-4-6"
# model_name = "kimi-k2.5-turbo"
plot_file_types = ["pdf", "png"]
input_file_path = "../data/summaries.csv"
output_folder_path = "../data/plots/by-agent-and-eval"

# Create the output folder
os.makedirs(output_folder_path, exist_ok=True)


def save_plot(file_path, **kwargs):
    file_stem, _ = os.path.splitext(file_path)
    for extension in plot_file_types:
        plt.savefig(f"{file_stem}.{extension}", **kwargs)

# Load the data
summaries = pd.read_csv(input_file_path)

# Filter rows
summaries = summaries[summaries["version"] == version]
summaries = summaries[summaries["model_name"] == model_name]
summaries = summaries[summaries["eval_name"].str.startswith("tw-")]

# Verify the summaries contain exactly one split
if summaries["split_name"].nunique() != 1:
    raise ValueError("Summaries contain both train and test evals.")

# Create groups
summaries = summaries.groupby(["agent_name", "model_name", "eval_name"], as_index=False).agg({
    "episodes": "sum",
    "successes": "sum",
    "total_steps": "sum",
    "total_tokens": "sum",
    "total_reward": "sum",
    "errors": "sum",
    "avg_reward_per_step": "mean",
    "avg_reward_per_token": "mean",
})

# Compute averages
summaries["accuracy"] = summaries["successes"] / summaries["episodes"]
summaries["avg_steps_per_episode"] = summaries["total_steps"] / summaries["episodes"]
summaries["avg_tokens_per_episode"] = summaries["total_tokens"] / summaries["episodes"]
summaries["avg_reward_per_episode"] = summaries["total_reward"] / summaries["episodes"]
summaries["avg_reward_per_m_tokens"] = summaries["avg_reward_per_token"] * 1_000_000

# Verify all groups have same number of episodes
if summaries["episodes"].nunique() != 1:
    raise ValueError("Not all groups have the same number of episodes")

# Order agents
agent_order = [
    "react-kn",
    "modular-full",
]

# Order agents
agent_order = [
    # "react-k1",
    "react-kn",
    # "modular-base",
    # "plus-planner",
    # "plus-summarizer",
    # "plus-memorizer",
    # "minus-planner",
    # "minus-summarizer",
    # "minus-memorizer",
    "modular-full",
]

summaries["agent_name"] = pd.Categorical(
    summaries["agent_name"],
    categories=agent_order,
    ordered=True)

# Order the eval names
eval_order = [
    "tw-simple-1",
    "tw-treasure-1",
    "tw-treasure-2",
    "tw-treasure-3",
    "tw-coin-1",
    "tw-coin-2",
    "tw-coin-3",
    "tw-cooking-1",
    "tw-cooking-2",
    "tw-cooking-3"
]
summaries["eval_name"] = pd.Categorical(
    summaries["eval_name"],
    categories=eval_order,
    ordered=True)

pastel = sns.color_palette("tab10")
palette = {
    name:
        pastel[7] if name.startswith("react") else      # grey
        pastel[0] if name.startswith("modular-base") else   # blue
        pastel[2] if name.startswith("plus") else       # green
        pastel[1] if name.startswith("minus") else      # orange
        pastel[0] if name.startswith("modular-full") else    # blue
        pastel[7]                                       # grey
    for name in agent_order
}

# Create plot for task completion accuracy
accuracy_file_name = f"accuracy-by-agent-and-eval-for-{model_name}.png"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="eval_name",
    y="accuracy",
    hue="agent_name",
    data=summaries,
    palette=palette)
plt.title(f"Accuracy by Agent and Eval with {model_name}")
plt.xlabel("Eval")
plt.ylabel("Accuracy (task completion rate)")
plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent")
save_plot(f"{output_folder_path}/{accuracy_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average steps per episode
steps_file_name = f"avg-steps-per-episode-by-agent-and-eval-for-{model_name}.png"
sns.set_style("whitegrid")
plt.figure(figsize=(14, 6))
ax = sns.barplot(
    x="eval_name",
    y="avg_steps_per_episode",
    hue="agent_name",
    data=summaries,
    palette=palette)
plt.title(f"Average Steps per Episode by Agent and Eval with {model_name}")
plt.xlabel("Eval")
plt.ylabel("Average steps per episode")
plt.xticks(rotation=45, ha='right')
plt.subplots_adjust(bottom=0.25)
plt.legend(title="Agent")
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}"))
save_plot(f"{output_folder_path}/{steps_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average tokens per episode
tokens_file_name = f"avg-tokens-per-episode-by-agent-and-eval-with-{model_name}.png"
sns.set_style("whitegrid")
plt.figure(figsize=(14, 6))
ax = sns.barplot(
    x="eval_name",
    y="avg_tokens_per_episode",
    hue="agent_name",
    data=summaries,
    palette=palette)
plt.title(f"Average Tokens by Agent and Eval with {model_name}")
plt.xlabel("Eval")
plt.ylabel("Average tokens per episode")
plt.xticks(rotation=45, ha='right')
plt.subplots_adjust(bottom=0.25)
plt.legend(title="Agent")
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}"))
save_plot(f"{output_folder_path}/{tokens_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average reward per episode
reward_file_name = f"avg-reward-per-episode-by-agent-and-eval-for-{model_name}.png"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="eval_name",
    y="avg_reward_per_episode",
    hue="agent_name",
    data=summaries,
    palette=palette)
plt.title(f"Average Reward per Episode by Agent and Eval with {model_name}")
plt.xlabel("Eval")
plt.ylabel("Average reward per episode")
plt.ylim(0.0, 1.0)
plt.xticks(rotation=45, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent")
save_plot(f"{output_folder_path}/{reward_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average reward per step
reward_per_step_file_name = f"avg-reward-per-step-by-agent-and-eval-for-{model_name}.png"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="eval_name",
    y="avg_reward_per_step",
    hue="agent_name",
    data=summaries,
    palette=palette)
plt.title(f"Average Reward per Step by Agent and Eval with {model_name}")
plt.xlabel("Eval")
plt.ylabel("Reward per step")
#plt.ylim(0.0, 1.0)
plt.xticks(rotation=45, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent")
save_plot(f"{output_folder_path}/{reward_per_step_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average reward per token
reward_per_token_file_name = f"reward-per-m-tokens-by-agent-and-eval-for-{model_name}.png"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="eval_name",
    y="avg_reward_per_m_tokens",
    hue="agent_name",
    data=summaries,
    palette=palette)
plt.title(f"Average Reward per Million Tokens by Agent and Eval with {model_name}")
plt.xlabel("Eval")
plt.ylabel("Average reward per million tokens")
#plt.ylim(0.0, 1.0)
plt.xticks(rotation=45, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent")
save_plot(f"{output_folder_path}/{reward_per_token_file_name}", bbox_inches='tight')
plt.show()

# Create plot for errors (all red to denote errors)
errors_file_name = f"errors-by-agent-and-eval-for-{model_name}.png"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
error_palette = {agent_name: "red" for agent_name in agent_order}
ax = sns.barplot(
    x="eval_name",
    y="errors",
    hue="agent_name",
    data=summaries,
    palette=error_palette)
plt.title(f"Errors by Agent and Eval with {model_name}")
plt.xlabel("Eval")
plt.ylabel("Errors")
plt.ylim(0, 100)
plt.xticks(rotation=45, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent")
for p in ax.patches:
    ax.annotate(f"{int(p.get_height()):,}", (p.get_x() + p.get_width() / 2, p.get_height()), ha='center', va='bottom', fontsize=9)
save_plot(f"{output_folder_path}/{errors_file_name}", bbox_inches='tight')
plt.show()

# Filter any agent names with nan
summaries = summaries[~summaries["agent_name"].isna()]

# Render a table in markdown
markdown_table = summaries[[
    "agent_name",
    "eval_name",
    "errors",
    "accuracy",
    "avg_steps_per_episode",
    "avg_tokens_per_episode",
    "avg_reward_per_episode",
    "avg_reward_per_step",
    "avg_reward_per_m_tokens"
]].to_markdown(index=False)
print(markdown_table)


