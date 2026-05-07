import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# Set parameters
input_file_path = "../data/summaries.csv"
output_folder_path = "../data/plots/by-model-and-agent"

# Create the output folder
os.makedirs(output_folder_path, exist_ok=True)


def save_plot(file_path, **kwargs):
    file_stem, _ = os.path.splitext(file_path)
    for extension in ("pdf", "png"):
        plt.savefig(f"{file_stem}.{extension}", **kwargs)

# Load the data
summaries = pd.read_csv(input_file_path)

# Filter rows
# summaries = summaries[summaries["model_name"] == model_name]
summaries = summaries[summaries["eval_name"].str.startswith("tw-")]

# Remove deepseek-v4
summaries = summaries[~summaries["model_name"].str.startswith("deepseek-v4", na=False)]

# Create groups
summaries = summaries.groupby(["model_name", "agent_name"], as_index=False).agg({
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

# Rename models
model_name_mapping = {
    "gemini-3.1-flash-preview": "gemini-3.1-flash",
    "gemini-3.1-pro-preview": "gemini-3.1-pro",
    "kimi-k2.5-turbo": "kimi-k2.5",
    "glm-5-fast": "glm-5"}
summaries["model_name"] = summaries["model_name"].replace(model_name_mapping)

# Order models
model_order = [
    "claude-sonnet-4-6",
    "gemini-3.1-pro",
    "gpt-5.2",
    "gpt-5.4",
    "gpt-5.5",
    "glm-5",
    "kimi-k2.5",
    "qwen3.6-plus",
]

# Filter out any models not in the list
summaries = summaries[summaries["model_name"].isin(model_order)]

summaries["model_name"] = pd.Categorical(
    summaries["model_name"],
    categories=model_order,
    ordered=True)

# Remove the version from the agent name
summaries["agent_name"] = summaries["agent_name"].str.removesuffix("-v5.0")

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
plt.ylabel("Accuracy (task completion rate)")
plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent")
save_plot(f"{output_folder_path}/{accuracy_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average steps per task
steps_file_name = f"avg-steps-per-task-by-model-and-agent.pdf"
sns.set_style("whitegrid")
plt.figure(figsize=(14, 6))
ax = sns.barplot(
    x="model_name",
    y="avg_steps_per_task",
    hue="agent_name",
    data=summaries,
    palette=palette)
plt.title(f"Average Steps per Task by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Average steps per task")
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.25)
plt.legend(title="Agent")
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}"))
save_plot(f"{output_folder_path}/{steps_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average tokens per task
tokens_file_name = f"avg-tokens-per-task-by-model-and-agent.pdf"
sns.set_style("whitegrid")
plt.figure(figsize=(14, 6))
ax = sns.barplot(
    x="model_name",
    y="avg_tokens_per_task",
    hue="agent_name",
    data=summaries,
    palette=palette)
plt.title(f"Average Tokens by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Average tokens per task")
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.25)
plt.legend(title="Agent")
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}"))
save_plot(f"{output_folder_path}/{tokens_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average reward per task
reward_file_name = f"avg-reward-per-task-by-model-and-agent.pdf"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="avg_reward_per_task",
    hue="agent_name",
    data=summaries,
    palette=palette)
plt.title(f"Average Reward per Task by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Average reward per task")
plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent")
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
plt.legend(title="Agent")
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
plt.legend(title="Agent")
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
plt.legend(title="Agent")
plt.ylim(0, 100)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
for p in ax.patches:
    ax.annotate(f"{int(p.get_height()):,}",(p.get_x() + p.get_width() / 2, p.get_height()), ha='center', va='bottom', fontsize=9)
save_plot(f"{output_folder_path}/{errors_file_name}", bbox_inches='tight')
plt.show()


# Create plot for total tasks
tasks_file_name = f"tasks-by-model-and-agent.pdf"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="tasks",
    hue="agent_name",
    data=summaries,
    palette=palette )
plt.title(f"Total Tasks by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Total tasks")
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent")
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}"))
save_plot(f"{output_folder_path}/{tasks_file_name}", bbox_inches='tight')
plt.show()

# Filter any agent names with nan
summaries = summaries[~summaries["agent_name"].isna()]

# Render a table
markdown_table = summaries[[
    "model_name",
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
accuracy_file_name = f"accuracy-by-model.pdf"
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
plt.legend(title="Agent")
plt.tight_layout()
save_plot(f"{output_folder_path}/{accuracy_file_name}", bbox_inches='tight')
plt.show()


