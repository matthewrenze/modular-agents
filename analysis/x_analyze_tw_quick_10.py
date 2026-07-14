import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# Set parameters
input_file_path = "../data/summaries.csv"
output_folder_path = "../data/plots/tw-quick-10"

# Create the output folder
os.makedirs(output_folder_path, exist_ok=True)

# Load the data
summaries = pd.read_csv(input_file_path)

# Filter rows
summaries = summaries[summaries["split_name"] == "train"]
# summaries = summaries[summaries["model_name"] == model_name]
summaries = summaries[summaries["eval_name"].str.startswith("tw-quick-1")]
# summaries = summaries[summaries["eval_size"] == 10]

# Create groups
summaries = summaries.groupby(["split_name", "model_name", "agent_name"], as_index=False).agg({
    "episodes": "sum",
    "successes": "sum",
    "total_steps": "sum",
    "total_tokens": "sum",
    "total_reward": "sum",
    "total_cost": "sum",
    "total_time": "sum",
    "errors": "sum",
})

# Compute averages
summaries["accuracy"] = summaries["successes"] / summaries["episodes"]
summaries["avg_steps_per_episode"] = summaries["total_steps"] / summaries["episodes"]
summaries["avg_tokens_per_episode"] = summaries["total_tokens"] / summaries["episodes"]
summaries["avg_reward_per_episode"] = summaries["total_reward"] / summaries["episodes"]
summaries["avg_reward_per_step"] = summaries["total_reward"] / summaries["total_steps"]
summaries["avg_reward_per_token"] = summaries["total_reward"] / summaries["total_tokens"]
summaries["avg_reward_per_m_tokens"] = summaries["avg_reward_per_token"] * 1_000_000

# # Verify all groups have same number of episodes
# if summaries["episodes"].nunique() != 1:
#     raise ValueError("Not all groups have the same number of episodes")

# Rename models
model_name_mapping = {
    "gemini-3.1-flash-preview": "gemini-3.1-flash",
    "gemini-3.1-pro-preview": "gemini-3.1-pro"}
summaries["model_name"] = summaries["model_name"].replace(model_name_mapping)

# Order models
model_order = [
    "gpt-5.4-mini",
    "gpt-5.2",
    "gpt-5.4",
    "claude-sonnet-4-6",
    "gemini-3.1-pro",
    "gpt-5.5",
    # "deepseek-v4",
    "kimi-k2.5-turbo",
    "glm-5-fast",
    "kimi-k2.6",
    "glm-5.1",
]

summaries["model_name"] = pd.Categorical(
    summaries["model_name"],
    categories=model_order,
    ordered=True)

# Order agents
agent_order = [
    "react-kn-v5.0",
    "modular-full-v5.0",
]

summaries["agent_name"] = pd.Categorical(
    summaries["agent_name"],
    categories=agent_order,
    ordered=True)

agent_label_mapping = {
    "react-kn-v5.0": "ReAct",
    "modular-full-v5.0": "Modular Full",
}

summaries["agent_label"] = summaries["agent_name"].map(agent_label_mapping)

agent_label_order = [
    "ReAct",
    "Modular Full",
]

palette = {
    "ReAct": "tab:grey",
    "Modular Full": "tab:blue",
}

# Create plot for task completion accuracy
accuracy_file_name = f"accuracy-by-model-and-agent.png"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="accuracy",
    hue="agent_label",
    hue_order=agent_label_order,
    data=summaries,
    palette=palette)
plt.title(f"Accuracy by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Accuracy (task completion rate)")
plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent")
plt.savefig(f"{output_folder_path}/{accuracy_file_name}", bbox_inches='tight')
plt.show()

# Create plot for average reward per step
reward_per_step_file_name = f"avg-reward-per-step-by-model-and-agent.png"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="avg_reward_per_step",
    hue="agent_label",
    hue_order=agent_label_order,
    data=summaries,
    palette=palette,)
plt.title(f"Average Reward per Step by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Reward per step")
#plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent")
plt.savefig(f"{output_folder_path}/{reward_per_step_file_name}", bbox_inches='tight')
plt.show()

# # Create plot for average reward per token
# reward_per_token_file_name = f"reward-per-m-tokens-by-model-and-agent.png"
# sns.set_style("whitegrid")
# plt.figure(figsize=(12, 6))
# ax = sns.barplot(
#     x="model_name",
#     y="avg_reward_per_m_tokens",
#     hue="agent_name",
#     data=summaries)
# plt.title(f"Average Reward per Million Tokens by Model and Agent")
# plt.xlabel("Model")
# plt.ylabel("Average reward per million tokens")
# #plt.ylim(0.0, 1.0)
# plt.xticks(rotation=15, ha='right')
# plt.subplots_adjust(bottom=0.2)
# plt.legend(title="Agent")
# plt.savefig(f"{output_folder_path}/{reward_per_token_file_name}", bbox_inches='tight')
# plt.show()

# Create plot for total runtime
reward_per_token_file_name = f"runtime-by-model-and-agent.png"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="total_time",
    hue="agent_label",
    hue_order=agent_label_order,
    data=summaries,
    palette=palette,)
plt.title(f"Total Runtime by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Total Runtime (seconds)")
#plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent")
plt.savefig(f"{output_folder_path}/{reward_per_token_file_name}", bbox_inches='tight')
plt.show()

# Create plot for total cost
reward_per_token_file_name = f"cost-by-model-and-agent.png"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="total_cost",
    hue="agent_label",
    hue_order=agent_label_order,
    data=summaries,
    palette=palette,)
plt.title(f"Total Cost by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Total Cost ($USD)")
#plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
plt.legend(title="Agent")
plt.savefig(f"{output_folder_path}/{reward_per_token_file_name}", bbox_inches='tight')
plt.show()

# Create plot for errors (all red to denote errors)
errors_file_name = f"errors-by-model-and-agent.png"
sns.set_style("whitegrid")
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="errors",
    hue="agent_name",
    data=summaries,
    palette='dark:red')
plt.title(f"Errors by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Errors")
plt.legend(title="Agent")
plt.ylim(0, 100)
plt.xticks(rotation=15, ha='right')
plt.subplots_adjust(bottom=0.2)
for p in ax.patches:
    ax.annotate(f"{int(p.get_height()):,}",(p.get_x() + p.get_width() / 2, p.get_height()), ha='center', va='bottom', fontsize=9)
plt.savefig(f"{output_folder_path}/{errors_file_name}", bbox_inches='tight')
plt.show()

# Render a table
markdown_table = summaries[[
    "model_name",
    "agent_name",
    "avg_reward_per_step",
    "total_time",
    "total_cost"]] \
    .to_markdown(index=False, floatfmt=".2f")
print(markdown_table)


