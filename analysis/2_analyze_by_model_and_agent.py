import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.container import BarContainer
from matplotlib.ticker import FuncFormatter

# Set parameters
version = "v6.0"
plot_file_types = ["pdf", "png"]
input_file_path = "../data/summaries.csv"
output_folder_path = "../data/plots/by-model-and-agent"

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
# summaries = summaries[summaries["model_name"] == model_name]
summaries = summaries[summaries["eval_name"].str.startswith("tw-")]

# Verify the summaries contain exactly one split
if summaries["split_name"].nunique() != 1:
    raise ValueError("Summaries contain both train and test evals.")

# Remove deepseek-v4
summaries = summaries[~summaries["model_name"].str.startswith("deepseek-v4", na=False)]

# Create groups
summaries = summaries.groupby(["model_name", "agent_name"], as_index=False).agg({
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

# Rename models
model_name_mapping = {
    "gemini-3.1-flash-preview": "gemini-3.1-flash",
    "gemini-3.1-pro-preview": "gemini-3.1-pro",
    "kimi-k2.5-turbo": "kimi-k2.5",
    "glm-5-fast": "glm-5"}
summaries["model_name"] = summaries["model_name"].replace(model_name_mapping)

# Order models
model_order = [
    # "claude-sonnet-4-6",
    # "gemini-3.1-pro",
    # "gpt-5.2",
    "gpt-5.4",
    # "gpt-5.5",
    # "glm-5",
    # "kimi-k2.5",
    # "qwen3.6-plus",
]

# Filter out any models not in the list
summaries = summaries[summaries["model_name"].isin(model_order)]

summaries["model_name"] = pd.Categorical(
    summaries["model_name"],
    categories=model_order,
    ordered=True)

# Order agents
agent_order = [
    "react-kn",
    "modular-full",
]

summaries["agent_name"] = pd.Categorical(
    summaries["agent_name"],
    categories=agent_order,
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

# Set the theme
sns.set_theme(
    style="whitegrid",
    font="sanserif",
    font_scale=1.25)

# Create plot for task completion accuracy
accuracy_file_name = f"accuracy-by-model-and-agent.pdf"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="accuracy",
    hue="agent_name",
    data=summaries,
    palette=palette)
plt.title(f"Accuracy by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Accuracy")
plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent", loc="lower right")
for container, agent_name in zip([c for c in ax.containers if isinstance(c, BarContainer)], agent_order):
    values = summaries[summaries["agent_name"] == agent_name].set_index("model_name")["accuracy"]
    labels = ["" if pd.isna(values.get(model_name)) else f"{values.get(model_name):.2f}" for model_name in model_order]
    ax.bar_label(container, labels=labels, padding=3, fontsize=9)
save_plot(f"{output_folder_path}/{accuracy_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average steps per episode
steps_file_name = f"avg-steps-per-episode-by-model-and-agent.pdf"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="avg_steps_per_episode",
    hue="agent_name",
    data=summaries,
    palette=palette)
plt.title(f"Average Steps per Episode by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Average steps per episode")
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.25)
plt.legend(title="Agent", loc="lower right")
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}"))
for container, agent_name in zip([c for c in ax.containers if isinstance(c, BarContainer)], agent_order):
    values = summaries[summaries["agent_name"] == agent_name].set_index("model_name")["avg_steps_per_episode"]
    labels = ["" if pd.isna(values.get(model_name)) else f"{int(values.get(model_name)):,}" for model_name in model_order]
    ax.bar_label(container, labels=labels, padding=3, fontsize=9)
save_plot(f"{output_folder_path}/{steps_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average tokens per episode
tokens_file_name = f"avg-tokens-per-episode-by-model-and-agent.pdf"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="avg_tokens_per_episode",
    hue="agent_name",
    data=summaries,
    palette=palette)
plt.title(f"Average Tokens by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Average tokens per episode (millions)")
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.25)
plt.legend(title="Agent", loc="upper center")
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x / 1_000_000:.1f}M"))
for container, agent_name in zip([c for c in ax.containers if isinstance(c, BarContainer)], agent_order):
    values = summaries[summaries["agent_name"] == agent_name].set_index("model_name")["avg_tokens_per_episode"]
    labels = ["" if pd.isna(values.get(model_name)) else f"{values.get(model_name) / 1_000_000:.2f}M" for model_name in model_order]
    ax.bar_label(container, labels=labels, padding=3, fontsize=9)
save_plot(f"{output_folder_path}/{tokens_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average reward per episode
reward_file_name = f"avg-reward-per-episode-by-model-and-agent.pdf"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="avg_reward_per_episode",
    hue="agent_name",
    data=summaries,
    palette=palette)
plt.title(f"Average Reward per Episode by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Average reward per episode")
plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent", loc="lower right")
for container, agent_name in zip([c for c in ax.containers if isinstance(c, BarContainer)], agent_order):
    values = summaries[summaries["agent_name"] == agent_name].set_index("model_name")["avg_reward_per_episode"]
    labels = ["" if pd.isna(values.get(model_name)) else f"{values.get(model_name):.2f}" for model_name in model_order]
    ax.bar_label(container, labels=labels, padding=3, fontsize=9)
save_plot(f"{output_folder_path}/{reward_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average reward per step
reward_per_step_file_name = f"avg-reward-per-step-by-model-and-agent.pdf"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="avg_reward_per_step",
    hue="agent_name",
    data=summaries,
    palette=palette)
plt.title(f"Average Reward per Step by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Reward per step")
#plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent", loc="lower right")
for container, agent_name in zip([c for c in ax.containers if isinstance(c, BarContainer)], agent_order):
    values = summaries[summaries["agent_name"] == agent_name].set_index("model_name")["avg_reward_per_step"]
    labels = ["" if pd.isna(values.get(model_name)) else f"{values.get(model_name):.4f}" for model_name in model_order]
    ax.bar_label(container, labels=labels, padding=3, fontsize=9)
save_plot(f"{output_folder_path}/{reward_per_step_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average reward per token
reward_per_token_file_name = f"reward-per-m-tokens-by-model-and-agent.pdf"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="avg_reward_per_m_tokens",
    hue="agent_name",
    data=summaries,
    palette=palette)
plt.title(f"Average Reward per Million Tokens by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Average reward per million tokens")
#plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent", loc="upper right")
for container, agent_name in zip([c for c in ax.containers if isinstance(c, BarContainer)], agent_order):
    values = summaries[summaries["agent_name"] == agent_name].set_index("model_name")["avg_reward_per_m_tokens"]
    labels = ["" if pd.isna(values.get(model_name)) else f"{values.get(model_name):.2f}" for model_name in model_order]
    ax.bar_label(container, labels=labels, padding=3, fontsize=9)
save_plot(f"{output_folder_path}/{reward_per_token_file_name}", bbox_inches='tight')
plt.show()

# Create plot for errors (all red to denote errors)
errors_file_name = f"errors-by-model-and-agent.pdf"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="errors",
    hue="agent_name",
    data=summaries,
    color="red")
plt.title(f"Errors by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Errors")
plt.legend(title="Agent", loc="upper right")
plt.ylim(0, 100)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
for container, agent_name in zip([c for c in ax.containers if isinstance(c, BarContainer)], agent_order):
    values = summaries[summaries["agent_name"] == agent_name].set_index("model_name")["errors"]
    labels = ["" if pd.isna(values.get(model_name)) else f"{int(values.get(model_name)):,}" for model_name in model_order]
    ax.bar_label(container, labels=labels, padding=3, fontsize=9)
save_plot(f"{output_folder_path}/{errors_file_name}", bbox_inches='tight')
plt.show()


# Create plot for total episodes
episodes_file_name = f"episodes-by-model-and-agent.pdf"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="episodes",
    hue="agent_name",
    data=summaries,
    palette=palette )
plt.title(f"Total Episodes by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Total episodes")
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent", loc="lower right")
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}"))
for container, agent_name in zip([c for c in ax.containers if isinstance(c, BarContainer)], agent_order):
    values = summaries[summaries["agent_name"] == agent_name].set_index("model_name")["episodes"]
    labels = ["" if pd.isna(values.get(model_name)) else f"{int(values.get(model_name)):,}" for model_name in model_order]
    ax.bar_label(container, labels=labels, padding=3, fontsize=9)
save_plot(f"{output_folder_path}/{episodes_file_name}", bbox_inches='tight')
plt.show()

# Filter any agent names with nan
summaries = summaries[~summaries["agent_name"].isna()]

# Render a table
markdown_table = summaries[[
    "model_name",
    "agent_name",
    "accuracy",
    "avg_steps_per_episode",
    "avg_tokens_per_episode",
    "avg_reward_per_episode",
    "avg_reward_per_step",
    "avg_reward_per_m_tokens"]] \
    .to_markdown(index=False, floatfmt=".2f")
print(markdown_table)


### NeurIPS Plot

# Create plot for accuracy
sns.set_theme(
    style="whitegrid",
    font="serif",
    font_scale=1.25,
    rc={
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
        "mathtext.fontset": "dejavuserif",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    },
)
accuracy_file_name = f"accuracy-by-model-neurips.pdf"
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="accuracy",
    hue="agent_name",
    data=summaries,
    palette=palette)
plt.xlabel("Model")
ax.set_ylabel("Accuracy")
plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent", loc="lower right")
for container, agent_name in zip([c for c in ax.containers if isinstance(c, BarContainer)], agent_order):
    values = summaries[summaries["agent_name"] == agent_name].set_index("model_name")["accuracy"]
    labels = ["" if pd.isna(values.get(model_name)) else f"{values.get(model_name):.2f}" for model_name in model_order]
    ax.bar_label(container, labels=labels, padding=3, fontsize=9)
plt.tight_layout()
save_plot(f"{output_folder_path}/{accuracy_file_name}", bbox_inches='tight')
plt.show()


