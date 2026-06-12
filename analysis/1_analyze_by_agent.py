import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# Hide future warnings
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Set parameters
model_name = "gpt-5.4"
version_suffix = "-v6.0"
plot_file_types = ["pdf", "png"]
input_file_path = "../data/summaries.csv"
output_folder_path = "../data/plots/by-agent"

# Create the output folder
os.makedirs(output_folder_path, exist_ok=True)


def save_plot(file_name):
    for extension in plot_file_types:
        plt.savefig(os.path.join(output_folder_path, f"{file_name}.{extension}"), bbox_inches='tight')

# Load the data
summaries = pd.read_csv(input_file_path)

# Filter rows
summaries = summaries[summaries["model_name"] == model_name]
summaries = summaries[summaries["eval_name"].str.startswith("tw-")]

# Create groups
summaries = summaries.groupby(["agent_name", "model_name"], as_index=False).agg({
    "tasks": "sum",
    "successes": "sum",
    "total_steps": "sum",
    "total_tokens": "sum",
    "total_reward": "sum",
    "errors": "sum",
})

# Compute averages
summaries["accuracy"] = summaries["successes"] / summaries["tasks"]
summaries["avg_steps_per_task"] = summaries["total_steps"] / summaries["tasks"]
summaries["avg_tokens_per_task"] = summaries["total_tokens"] / summaries["tasks"]
summaries["avg_reward_per_task"] = summaries["total_reward"] / summaries["tasks"]
summaries["avg_reward_per_step"] = summaries["total_reward"] / summaries["total_steps"]
summaries["avg_reward_per_token"] = summaries["total_reward"] / summaries["total_tokens"]
summaries["avg_reward_per_m_tokens"] = summaries["avg_reward_per_token"] * 1_000_000

# Verify all groups have same number of episodes
if summaries["tasks"].nunique() != 1:
    raise ValueError("Not all groups have the same number of tasks")

# Remove the version from the agent name
summaries["agent_name"] = summaries["agent_name"].str.removesuffix(version_suffix)

# Order agents
agent_order = [
    "react-k1",
    "react-kn",
    "modular-base",
    "plus-planner",
    "plus-summarizer",
    "plus-memorizer",
    "minus-planner",
    "minus-summarizer",
    "minus-memorizer",
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

# Create plot for accuracy
accuracy_file_name = f"accuracy-by-agent-for-{model_name}"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="agent_name",
    y="accuracy",
    data=summaries,
    palette=palette)
plt.title(f"Accuracy by Agent with {model_name}")
plt.xlabel("Agent")
plt.ylabel("Accuracy")
plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
for p in ax.patches:
    ax.annotate(f"{p.get_height():.2f}",(p.get_x() + p.get_width() / 2, p.get_height()), ha='center', va='bottom', fontsize=9)
plt.tight_layout()
save_plot(accuracy_file_name)
plt.show()

# Create plot for average steps per task
steps_file_name = f"avg-steps-per-task-by-agent-for-{model_name}"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="agent_name",
    y="avg_steps_per_task",
    data=summaries,
    palette=palette)
plt.title(f"Average Steps per Task by Agent with {model_name}")
plt.xlabel("Agent")
plt.ylabel("Average steps per task")
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}"))
for p in ax.patches:
    ax.annotate(f"{int(p.get_height()):,}",(p.get_x() + p.get_width() / 2, p.get_height()), ha='center', va='bottom', fontsize=9)
plt.tight_layout()
save_plot(steps_file_name)
plt.show()

# Create plot for average tokens per task
tokens_file_name = f"avg-tokens-per-task-by-agent-with-{model_name}"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="agent_name",
    y="avg_tokens_per_task",
    data=summaries,
    palette=palette)
plt.title(f"Average Tokens by Agent with {model_name}")
plt.xlabel("Agent")
plt.ylabel("Average tokens per task")
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}"))
for p in ax.patches:
    ax.annotate(f"{int(p.get_height()):,}",(p.get_x() + p.get_width() / 2, p.get_height()), ha='center', va='bottom', fontsize=9)
plt.tight_layout()
save_plot(tokens_file_name)
plt.show()

# Create plot for average reward per task
reward_file_name = f"avg-reward-per-task-by-agent-for-{model_name}"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="agent_name",
    y="avg_reward_per_task",
    data=summaries,
    palette=palette)
plt.title(f"Average Reward per Task by Agent with {model_name}")
plt.xlabel("Agent")
plt.ylabel("Average reward per task")
plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
for p in ax.patches:
    ax.annotate(f"{p.get_height():.2f}",(p.get_x() + p.get_width() / 2, p.get_height()), ha='center', va='bottom', fontsize=9)
plt.tight_layout()
save_plot(reward_file_name)
plt.show()

# Create plot for average reward per step
reward_per_step_file_name = f"avg-reward-per-step-by-agent-for-{model_name}"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="agent_name",
    y="avg_reward_per_step",
    data=summaries,
    palette=palette)
plt.title(f"Average Reward per Step by Agent with {model_name}")
plt.xlabel("Agent")
plt.ylabel("Reward per step")
#plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
for p in ax.patches:
    ax.annotate(f"{p.get_height():.4f}",(p.get_x() + p.get_width() / 2, p.get_height()), ha='center', va='bottom', fontsize=9)
plt.tight_layout()
save_plot(reward_per_step_file_name)
plt.show()

# Create plot for average reward per million tokens
reward_per_million_file_name = f"avg-reward-per-m-tokens-by-agent-for-{model_name}"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="agent_name",
    y="avg_reward_per_m_tokens",
    data=summaries,
    palette=palette)
plt.title(f"Average Reward per Million Tokens by Agent with {model_name}")
plt.xlabel("Agent")
plt.ylabel("Average reward per million tokens")
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
for p in ax.patches:
    ax.annotate(f"{p.get_height():.2f}", (p.get_x() + p.get_width() / 2, p.get_height()), ha='center', va='bottom', fontsize=9)
plt.tight_layout()
save_plot(reward_per_million_file_name)
plt.show()

# Create plot for errors (all red to denote errors)
accuracy_file_name = f"errors-by-agent-for-{model_name}"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="agent_name",
    y="errors",
    data=summaries,
    color="red")
plt.title(f"Errors by Agent with {model_name}")
plt.xlabel("Agent")
plt.ylabel("Errors")
plt.ylim(0, 100)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
for p in ax.patches:
    ax.annotate(f"{int(p.get_height()):,}",(p.get_x() + p.get_width() / 2, p.get_height()), ha='center', va='bottom', fontsize=9)
plt.tight_layout()
save_plot(accuracy_file_name)
plt.show()

# Filter any agent names with nan
summaries = summaries[~summaries["agent_name"].isna()]

# Render a table
markdown_table = summaries[[
    "agent_name",
    "accuracy",
    "avg_steps_per_task",
    "avg_tokens_per_task",
    "avg_reward_per_task",
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
accuracy_file_name = f"accuracy-by-agent-neurips"
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="agent_name",
    y="accuracy",
    data=summaries,
    palette=palette)
plt.xlabel("Agent")
plt.ylabel("Accuracy")
plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
for p in ax.patches:
    ax.annotate(f"{p.get_height():.2f}",(p.get_x() + p.get_width() / 2, p.get_height()), ha='center', va='bottom', fontsize=9)
plt.tight_layout()
save_plot(accuracy_file_name)
plt.show()

