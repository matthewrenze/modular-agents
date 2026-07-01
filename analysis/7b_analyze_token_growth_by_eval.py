import os
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import seaborn as sns


warnings.simplefilter(action="ignore", category=FutureWarning)

version = "v6.0"
split_name = "train"
model_name = "gpt-5.4"

agent_names = [
    "react-kn",
    "modular-full",
]

marginal_trend_degrees = {
    "react-kn": 1,
    "modular-full": 1,
}

cumulative_trend_degrees = {
    "react-kn": 2,
    "modular-full": 2,
}

eval_names = [
    "tw-simple-1",
    "tw-treasure-1",
    "tw-treasure-2",
    "tw-treasure-3",
    "tw-coin-1",
    "tw-coin-2",
    "tw-coin-3",
    "tw-cooking-1",
    "tw-cooking-2",
    "tw-cooking-3",
]

pastel = sns.color_palette("tab10")
agent_palette = {
    name:
        pastel[7] if name.startswith("react") else      # grey
        pastel[0] if name.startswith("modular-full") else   # blue
        pastel[7]
    for name in agent_names
}
eval_line_styles = {
    eval_name: line_style
    for eval_name, line_style in zip(
        eval_names,
        [
            "-",
            "--",
            "-.",
            ":",
            (0, (5, 1)),
            (0, (3, 1, 1, 1)),
            (0, (1, 1)),
            (0, (5, 2, 1, 2)),
            (0, (3, 5, 1, 5)),
            (0, (7, 2)),
        ],
    )
}

root_folder_path = f"../data/artifacts/{version}/{split_name}"
plot_folder_path = "../data/plots/token-growth"
marginal_plot_file_path = f"{plot_folder_path}/marginal-token-growth-by-steps-for-{model_name}-by-eval.png"
cumulative_plot_file_path = f"{plot_folder_path}/cumulative-token-growth-by-steps-for-{model_name}-by-eval.png"

# Create the plot folder
os.makedirs(plot_folder_path, exist_ok=True)


def save_plot(file_path, **kwargs):
    file_stem, _ = os.path.splitext(file_path)
    for extension in ("pdf", "png"):
        plt.savefig(f"{file_stem}.{extension}", **kwargs)

# Get the details file paths
details_file_paths = list(Path(root_folder_path).rglob("*details.csv"))

# Load all the details data
frames = []
skipped_file_paths = []

for f in details_file_paths:
    if not f.exists():
        skipped_file_paths.append(str(f))
        continue

    try:
        frame = pd.read_csv(f)
    except FileNotFoundError:
        skipped_file_paths.append(str(f))
        continue

    file_name_parts = f.stem.split(" - ")
    split_name_parsed = file_name_parts[1]
    model_name_parsed = file_name_parts[2]
    agent_name_parsed = file_name_parts[3]
    eval_name_parsed = file_name_parts[4]
    episode_id = int(file_name_parts[5].replace("episode-", ""))

    frame["split_name"] = split_name_parsed
    frame["model_name"] = model_name_parsed
    frame["agent_name"] = agent_name_parsed
    frame["eval_name"] = eval_name_parsed
    frame["episode_id"] = episode_id
    frame["source_file"] = str(f)

    frames.append(frame)

if not frames:
    raise FileNotFoundError(f"No readable details files were found under {root_folder_path}.")

all_details = pd.concat(frames, ignore_index=True)

print(f"Loaded {len(all_details):,} rows from {len(details_file_paths):,} artifact result files.")
if skipped_file_paths:
    print(f"Skipped {len(skipped_file_paths):,} missing artifact files.")


# Filter the details
all_details = all_details[all_details["split_name"] == split_name]
all_details = all_details[all_details["model_name"] == model_name]
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


def fit_trend_model(details: pd.DataFrame, y_column: str, configured_degree: int):
    unique_step_count = details["step_id"].nunique()
    if len(details) < 2 or unique_step_count < 2:
        return None

    trend_degree = min(configured_degree, unique_step_count - 1)
    if trend_degree < 1:
        return None

    return np.poly1d(np.polyfit(
        details["step_id"],
        details[y_column],
        deg=trend_degree,
    ))


def plot_combo_trend_lines(details: pd.DataFrame, projection_steps: pd.DataFrame, y_column: str, trend_degrees: dict):
    for agent_name in agent_names:
        for eval_name in eval_names:
            combo_details = details[
                (details["agent_name"] == agent_name)
                & (details["eval_name"] == eval_name)
            ]
            configured_degree = trend_degrees.get(agent_name, 1)
            trend_model = fit_trend_model(combo_details, y_column, configured_degree)
            if trend_model is None:
                continue

            projection = projection_steps.copy()
            projection[y_column] = trend_model(projection["step_id"])

            sns.lineplot(
                data=projection,
                x="step_id",
                y=y_column,
                label=f"{agent_name} | {eval_name}",
                color=agent_palette[agent_name],
                linestyle=eval_line_styles[eval_name],
                linewidth=2,
            )


def show_plot_if_interactive():
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="FigureCanvasAgg is non-interactive, and thus cannot be shown",
            category=UserWarning,
        )
        plt.show()


# Create marginal scatter plot
plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=all_details,
    x="step_id",
    y="total_tokens",
    hue="agent_name",
    hue_order=agent_names,
    palette=agent_palette,
    alpha=0.1,
    legend=False,
)

# Create marginal trend lines
projection_steps = pd.DataFrame({"step_id": np.arange(1, 201)})
plot_combo_trend_lines(
    details=all_details,
    projection_steps=projection_steps,
    y_column="total_tokens",
    trend_degrees=marginal_trend_degrees,
)

plt.title(f"Marginal Token Growth by Step - {model_name}")
plt.xlabel("Step")
plt.ylabel("Tokens per Step")
plt.xlim(0, 200)
plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
plt.legend(title="Trend (agent | eval)", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
save_plot(marginal_plot_file_path, dpi=300)
show_plot_if_interactive()
plt.close()


# Create cumulative scatter plot
plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=all_details,
    x="step_id",
    y="cumulative_tokens",
    hue="agent_name",
    hue_order=agent_names,
    palette=agent_palette,
    alpha=0.1,
    legend=False,
)

# Create cumulative trend lines
projection_steps = pd.DataFrame({"step_id": np.arange(1, 301)})
plot_combo_trend_lines(
    details=all_details,
    projection_steps=projection_steps,
    y_column="cumulative_tokens",
    trend_degrees=cumulative_trend_degrees,
)

plt.title(f"Cumulative Token Growth by Step - {model_name}")
plt.xlabel("Step")
plt.ylabel("Cumulative Tokens (millions)")
plt.xlim(0, 300)
plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x / 1_000_000:,.1f}"))
plt.legend(title="Trend (agent | eval)", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
save_plot(cumulative_plot_file_path, dpi=300)
show_plot_if_interactive()
plt.close()
