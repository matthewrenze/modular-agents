import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# Hide future warnings
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Set parameters
model_name = "gpt-5.2"
input_v1_file_path = "../data/summaries-v1.csv"
input_v2_file_path = "../data/summaries-v2.csv"
input_v3_file_path = "../data/summaries-v3.csv"
input_v4_file_path = "../data/summaries.csv"
output_folder_path = "../data/plots/by-version"

# Create the output folder
os.makedirs(output_folder_path, exist_ok=True)

# Load the data
summaries_v1 = pd.read_csv(input_v1_file_path)
summaries_v2 = pd.read_csv(input_v2_file_path)
summaries_v3 = pd.read_csv(input_v3_file_path)
summaries_v4 = pd.read_csv(input_v4_file_path)

# Merge the data
all_summaries = [summaries_v1, summaries_v2, summaries_v3, summaries_v4]
all_summaries = pd.concat(all_summaries, ignore_index=True)

# Rename agents
all_summaries["agent_name"] = all_summaries["agent_name"].str.replace("baseline", "modular-base", regex=False)
all_summaries["agent_name"] = all_summaries["agent_name"].str.replace("topline", "modular-full", regex=False)

# Filter rows
all_summaries = all_summaries[all_summaries["model_name"] == model_name]
all_summaries = all_summaries[all_summaries["eval_name"].str.startswith("tw-")]

# Create groups
all_summaries = all_summaries.groupby(["agent_name", "model_name"], as_index=False).agg({
    "tasks": "sum",
    "successes": "sum",
    "total_steps": "sum",
    "total_tokens": "sum",
    "total_reward": "sum",
})

# Compute averages
all_summaries["accuracy"] = all_summaries["successes"] / all_summaries["tasks"]
all_summaries["avg_steps_per_task"] = all_summaries["total_steps"] / all_summaries["tasks"]
all_summaries["avg_tokens_per_task"] = all_summaries["total_tokens"] / all_summaries["tasks"]
all_summaries["avg_reward_per_task"] = all_summaries["total_reward"] / all_summaries["tasks"]
all_summaries["avg_reward_per_step"] = all_summaries["total_reward"] / all_summaries["total_steps"]
all_summaries["avg_reward_per_token"] = all_summaries["total_reward"] / all_summaries["total_tokens"]
all_summaries["avg_reward_per_m_tokens"] = all_summaries["avg_reward_per_token"] * 1_000_000

# Verify all groups have same number of episodes
if all_summaries["tasks"].nunique() != 1:
    raise ValueError("Not all groups have the same number of tasks")

agent_bases = [
    "react-k0",
    "react-k1",
    "react-kn",
    "modular-base",
    "plus-planner",
    "plus-summarizer",
    "plus-memorizer",
    "plus-reasoner",
    "modular-full"]

for agent_base in agent_bases:

    # Copy the summaries
    summaries = all_summaries.copy()

    # Filter the agents
    summaries = summaries[summaries["agent_name"].str.contains(agent_base)]

    # Create plot for task completion accuracy
    accuracy_file_name = f"accuracy-by-version-for-{agent_base}-using-{model_name}.png"
    sns.set_style("whitegrid")
    plt.figure(figsize=(12, 6))
    ax = sns.barplot(
        x="agent_name",
        y="accuracy",
        data=summaries)
    plt.title(f"Accuracy by Version for {agent_base} with {model_name}")
    plt.xlabel("Agent")
    plt.ylabel("Accuracy (task completion rate)")
    plt.ylim(0.0, 1.0)
    plt.xticks(rotation=15, ha='right')
    plt.subplots_adjust(bottom=0.2)
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.1%}",(p.get_x() + p.get_width() / 2, p.get_height()), ha='center', va='bottom', fontsize=9)
    plt.savefig(f"{output_folder_path}/{accuracy_file_name}", bbox_inches='tight')
    plt.show()

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


