import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# Set parameters
# model_name = "gpt-5.2"
# model_name = "gpt-5-mini"
input_file_path = "../data/summaries.csv"
output_folder_path = "../data/plots/by-model-and-agent"

# Create the output folder
os.makedirs(output_folder_path, exist_ok=True)

# Load the data
summaries = pd.read_csv(input_file_path)

# Filter rows
# summaries = summaries[summaries["model_name"] == model_name]
summaries = summaries[summaries["eval_name"].str.startswith("tw-")]

# Create groups
summaries = summaries.groupby(["model_name", "agent_name"], as_index=False).agg({
    "tasks": "sum",
    "successes": "sum",
    "total_steps": "sum",
    "total_tokens": "sum",
    "total_reward": "sum",
})

# Compute averages
summaries["accuracy"] = summaries["successes"] / summaries["tasks"]
summaries["avg_steps_per_task"] = summaries["total_steps"] / summaries["tasks"]
summaries["avg_tokens_per_task"] = summaries["total_tokens"] / summaries["tasks"]
summaries["avg_reward_per_task"] = summaries["total_reward"] / summaries["tasks"]
summaries["avg_reward_per_step"] = summaries["total_reward"] / summaries["total_steps"]
summaries["avg_reward_per_token"] = summaries["total_reward"] / summaries["total_tokens"]
summaries["avg_reward_per_m_tokens"] = summaries["avg_reward_per_token"] * 1_000_000

# # Verify all groups have same number of episodes
# if summaries["tasks"].nunique() != 1:
#     raise ValueError("Not all groups have the same number of tasks")

# Rename models
model_name_mapping = {
    "gemini-3-flash-preview": "gemini-3-flash",
    "gemini-3-pro-preview": "gemini-3-pro"}
summaries["model_name"] = summaries["model_name"].replace(model_name_mapping)

# Order models
model_order = [
    "gpt-5-mini",
    "kimi-k2.5",
    "claude-sonnet-4-6",
    "gpt-5.2",
    "glm-5",
]

summaries["model_name"] = pd.Categorical(
    summaries["model_name"],
    categories=model_order,
    ordered=True)

# Order agents
agent_order = [
    # "react-k0-v3.0",
    # "react-k1-v3.0",
    "react-kn-v3.0",
    "baseline-v3.0",
    "plus-planner-v3.1",
    "plus-summarizer-v3.0",
    "plus-memorizer-v3.1",
    "plus-reasoner-v3.0",
    # "minus-planner-v3.0",
    # "minus-summarizer-v3.0",
    # "minus-memorizer-v3.0",
    # "minus-reasoner-v3.0",
    "topline-v3.0",
]

summaries["agent_name"] = pd.Categorical(
    summaries["agent_name"],
    categories=agent_order,
    ordered=True)

# Create plot for task completion accuracy
accuracy_file_name = f"accuracy-by-model-and-agent.png"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="accuracy",
    hue="agent_name",
    data=summaries)
plt.title(f"Accuracy by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Accuracy (task completion rate)")
plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent")
plt.savefig(f"{output_folder_path}/{accuracy_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average steps per task
steps_file_name = f"avg-steps-per-task-by-model-and-agent.png"
sns.set_style("whitegrid")
plt.figure(figsize=(14, 6))
ax = sns.barplot(
    x="model_name",
    y="avg_steps_per_task",
    hue="agent_name",
    data=summaries)
plt.title(f"Average Steps per Task by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Average steps per task")
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.25)
plt.legend(title="Agent")
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}"))
plt.savefig(f"{output_folder_path}/{steps_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average tokens per task
tokens_file_name = f"avg-tokens-per-task-by-model-and-agent.png"
sns.set_style("whitegrid")
plt.figure(figsize=(14, 6))
ax = sns.barplot(
    x="model_name",
    y="avg_tokens_per_task",
    hue="agent_name",
    data=summaries)
plt.title(f"Average Tokens by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Average tokens per task")
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.25)
plt.legend(title="Agent")
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}"))
plt.savefig(f"{output_folder_path}/{tokens_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average reward per task
reward_file_name = f"avg-reward-per-task-by-model-and-agent.png"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="avg_reward_per_task",
    hue="agent_name",
    data=summaries)
plt.title(f"Average Reward per Task by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Average reward per task")
plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent")
plt.savefig(f"{output_folder_path}/{reward_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average reward per step
reward_per_step_file_name = f"avg-reward-per-step-by-model-and-agent.png"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="avg_reward_per_step",
    hue="agent_name",
    data=summaries)
plt.title(f"Average Reward per Step by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Reward per step")
#plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent")
plt.savefig(f"{output_folder_path}/{reward_per_step_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average reward per token
reward_per_token_file_name = f"reward-per-m-tokens-by-model-and-agent.png"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="avg_reward_per_m_tokens",
    hue="agent_name",
    data=summaries)
plt.title(f"Average Reward per Million Tokens by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Average reward per million tokens")
#plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent")
plt.savefig(f"{output_folder_path}/{reward_per_token_file_name}", bbox_inches='tight')
plt.show()