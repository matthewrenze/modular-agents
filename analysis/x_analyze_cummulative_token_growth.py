import os
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import seaborn as sns



warnings.simplefilter(action="ignore", category=FutureWarning)

split_name = "train"
model_name = "gpt-5.2"

agent_names = [
	"react-kn-v5.0",
	"modular-full-v5.0",
]

trend_degrees_by_agent = {
    "react-kn-v5.0": 2,
    "modular-full-v5.0": 1,
}

eval_names = [
	"tw-quick-1",
	# "tw-simple-1",
	# "tw-treasure-1",
	# "tw-treasure-2",
	# "tw-treasure-3",
	# "tw-coin-1",
	# "tw-coin-2",
	# "tw-coin-3",
	# "tw-cooking-1",
	# "tw-cooking-2",
	# "tw-cooking-3",
]

root_folder_path = f"../data/artifacts/{split_name}"
plot_folder_path = "../data/plots/token-growth"
plot_file_path = f"{plot_folder_path}/cumulative-token-growth-by-steps-for-{model_name}.png"

# Create the plot folder
os.makedirs(plot_folder_path, exist_ok=True)

# Get the details file paths
details_file_paths = list(Path(root_folder_path).rglob("*details.csv"))

# Load all the details data
frames = []

for f in Path(root_folder_path).rglob("*details.csv"):
    frame = pd.read_csv(f)
    file_name_parts = f.stem.split(" - ")
    split_name_parsed = file_name_parts[0]
    model_name_parsed = file_name_parts[1]
    agent_name_parsed = file_name_parts[2]
    eval_name_parsed = file_name_parts[3]
    episode_id = int(file_name_parts[4].replace("episode-", ""))

    frame["split_name"] = split_name_parsed
    frame["model_name"] = model_name_parsed
    frame["agent_name"] = agent_name_parsed
    frame["eval_name"] = eval_name_parsed
    frame["episode_id"] = episode_id
    frame["source_file"] = str(f)

    frames.append(frame)

all_details = pd.concat(frames, ignore_index=True)

print(f"Loaded {len(all_details):,} rows from {len(details_file_paths):,} artifact result files.")


# Filter the details
all_details = all_details[all_details["split_name"] == split_name]
# all_details = all_details[all_details["model_name"] == model_name]
all_details = all_details[all_details["agent_name"].isin(agent_names)]
all_details = all_details[all_details["eval_name"].isin(eval_names)]
all_details = all_details.sort_values([
    "split_name",
    "model_name",
    "agent_name",
    "eval_name",
    "episode_id",
    "step_id",
])
all_details["cumulative_tokens"] = (
    all_details
    .groupby(["split_name", "model_name", "agent_name", "eval_name", "episode_id"])["total_tokens"]
    .cumsum()
    .astype(int)
)

# Create scatter plot
plt.figure(figsize=(10, 6))
sns.scatterplot(
	data=all_details,
	x="step_id",
	y="cumulative_tokens",
	hue="agent_name",
	hue_order=agent_names,
	alpha=0.1
)

# Create trend lines projected to 1,000 steps
projection_steps = pd.DataFrame({"step_id": np.arange(1, 501)})

for agent_name in agent_names:
    agent_details = all_details[all_details["agent_name"] == agent_name]
    trend_degree = trend_degrees_by_agent.get(agent_name, 1)
    trend_model = np.poly1d(np.polyfit(
        agent_details["step_id"],
        agent_details["cumulative_tokens"],
        deg=trend_degree,
    ))
    projection = projection_steps.copy()
    projection["cumulative_tokens"] = trend_model(projection["step_id"])
    projection["agent_name"] = agent_name

    sns.lineplot(
        data=projection,
        x="step_id",
        y="cumulative_tokens",
        label=f"{agent_name} trend",
        linestyle="--"
    )

plt.title(f"Cumulative Token Growth by Step - {model_name}")
plt.xlabel("Step")
plt.ylabel("Cumulative Tokens (millions)")
plt.xlim(0, 500)
plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x / 1_000_000:,.1f}"))
plt.legend(title="Agent")
plt.tight_layout()
plt.savefig(plot_file_path, dpi=300)
plt.show()

