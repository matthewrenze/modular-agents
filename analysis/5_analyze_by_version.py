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
input_file_paths = [
    "../data/summaries-v1.csv",
    "../data/summaries-v2.csv",
    "../data/summaries-v3.csv",
    "../data/summaries-v4.csv",
    "../data/summaries-v5.csv",
    "../data/summaries.csv",
]
output_folder_path = "../data/plots/by-version"

# Create the output folder
os.makedirs(output_folder_path, exist_ok=True)

# Load the summaries
summaries_list = []
for input_file_path in input_file_paths:
    summaries = pd.read_csv(input_file_path)
    summaries_list.append(summaries)

# Merge the summaries
all_summaries = pd.concat(summaries_list, ignore_index=True)

# Rename agents
all_summaries["agent_name"] = all_summaries["agent_name"].str.replace("baseline", "modular-base", regex=False)
all_summaries["agent_name"] = all_summaries["agent_name"].str.replace("topline", "modular-full", regex=False)

# Filter rows
all_summaries = all_summaries[all_summaries["model_name"] == model_name]
all_summaries = all_summaries[all_summaries["eval_name"].str.startswith("tw-")]

# Create groups
all_summaries = all_summaries.groupby(["version", "agent_name", "model_name"], as_index=False).agg({
    "episodes": "sum",
    "successes": "sum",
    "total_steps": "sum",
    "total_tokens": "sum",
    "total_reward": "sum",
})

# Compute averages
all_summaries["accuracy"] = all_summaries["successes"] / all_summaries["episodes"]
all_summaries["avg_steps_per_episode"] = all_summaries["total_steps"] / all_summaries["episodes"]
all_summaries["avg_tokens_per_episode"] = all_summaries["total_tokens"] / all_summaries["episodes"]
all_summaries["avg_reward_per_episode"] = all_summaries["total_reward"] / all_summaries["episodes"]
all_summaries["avg_reward_per_step"] = all_summaries["total_reward"] / all_summaries["total_steps"]
all_summaries["avg_reward_per_token"] = all_summaries["total_reward"] / all_summaries["total_tokens"]
all_summaries["avg_reward_per_m_tokens"] = all_summaries["avg_reward_per_token"] * 1_000_000

# Verify all groups have same number of episodes
if all_summaries["episodes"].nunique() != 1:
    raise ValueError("Not all groups have the same number of episodes")

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
        x="version",
        y="accuracy",
        hue="agent_name",
        data=summaries)
    plt.title(f"Accuracy by Version for {agent_base} with {model_name}")
    plt.xlabel("Version")
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
        "version",
        "agent_name",
        "accuracy",
        "avg_steps_per_episode",
        "avg_tokens_per_episode",
        "avg_reward_per_episode",
        "avg_reward_per_step",
        "avg_reward_per_m_tokens"]] \
        .to_markdown(index=False, floatfmt=".2f")
    print(markdown_table)


