import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter


warnings.simplefilter(action="ignore", category=FutureWarning)


MODEL_NAME = "gpt-5.2"
AGENT_ORDER = [
	"react-kn-v4.0",
	"modular-full-v4.0",
]
EVAL_ORDER = [
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

# Resolve the project root (works in both scripts and REPL/IPython)
start_paths = []
file_path = globals().get("__file__")
if file_path:
	start_paths.append(Path(file_path).resolve().parent)
start_paths.append(Path.cwd().resolve())

ROOT_PATH = None
checked_paths = []
seen_paths = set()
for start_path in start_paths:
	for candidate in [start_path, *start_path.parents]:
		if candidate in seen_paths:
			continue
		seen_paths.add(candidate)
		checked_paths.append(str(candidate))
		if (candidate / "analysis").is_dir() and (candidate / "data" / "artifacts").is_dir():
			ROOT_PATH = candidate
			break
	if ROOT_PATH is not None:
		break

if ROOT_PATH is None:
	raise FileNotFoundError(
		"Could not locate the project root. "
		"Expected to find both 'analysis' and 'data/artifacts'. "
		f"Checked: {checked_paths}"
	)

ARTIFACTS_FOLDER_PATH = ROOT_PATH / "data" / "artifacts"
OUTPUT_FOLDER_PATH = ROOT_PATH / "data" / "plots" / "token-growth"
OUTPUT_FILE_PATH = OUTPUT_FOLDER_PATH / f"token-growth-by-steps-for-{MODEL_NAME}.png"

# Load the data
result_files = sorted(ARTIFACTS_FOLDER_PATH.rglob("*results.csv"))
if not result_files:
	raise FileNotFoundError(f"No results files found under {ARTIFACTS_FOLDER_PATH}")

frames = []
for result_file in result_files:
	frame = pd.read_csv(result_file)
	frame["source_file"] = str(result_file)
	frames.append(frame)

all_results = pd.concat(frames, ignore_index=True)
print(f"Loaded {len(all_results):,} rows from {len(result_files):,} artifact result files.")

# Check required columns
required_columns = {
	"model_name",
	"agent_name",
	"eval_name",
	"episode",
	"steps",
	"total_tokens",
}
missing_columns = required_columns.difference(all_results.columns)
if missing_columns:
	raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

# Filter rows
results = all_results.copy()
results = results[results["model_name"] == MODEL_NAME]
results = results[results["agent_name"].isin(AGENT_ORDER)]
results = results[results["eval_name"].isin(EVAL_ORDER)]
results = results[results["steps"].between(0, 100)]
results = results.dropna(subset=["steps", "total_tokens"])

results["agent_name"] = pd.Categorical(
	results["agent_name"],
	categories=AGENT_ORDER,
	ordered=True,
)
results["eval_name"] = pd.Categorical(
	results["eval_name"],
	categories=EVAL_ORDER,
	ordered=True,
)

results = results.sort_values(["agent_name", "eval_name", "episode"]).reset_index(drop=True)

print(
	f"Filtered to {len(results):,} task rows "
	f"from {results['source_file'].nunique():,} result files "
	f"for {MODEL_NAME}."
)
print()

# Validate coverage
expected_file_count = len(AGENT_ORDER) * len(EVAL_ORDER)
actual_file_count = results["source_file"].nunique()
if actual_file_count != expected_file_count:
	raise ValueError(
		f"Expected {expected_file_count} filtered results files, found {actual_file_count}."
	)

coverage = (
	results.groupby(["agent_name", "eval_name"], observed=True)
	.size()
	.rename("tasks")
	.reset_index()
)

if len(coverage) != expected_file_count:
	raise ValueError("Missing one or more agent/eval combinations in the filtered data.")

if coverage["tasks"].nunique() != 1 or coverage["tasks"].iloc[0] != 10:
	raise ValueError("Expected exactly 10 task rows for every agent/eval combination.")

if set(results["agent_name"].astype(str).unique()) != set(AGENT_ORDER):
	raise ValueError("Filtered data does not contain exactly the requested agents.")

if set(results["eval_name"].astype(str).unique()) != set(EVAL_ORDER):
	raise ValueError("Filtered data does not contain exactly the requested evals.")

print("Coverage by agent and eval:")
print(coverage.to_markdown(index=False))
print()

# Create groups
growth = (
	results.groupby(["agent_name", "steps"], observed=True, as_index=False)
	.agg(
		avg_total_tokens=("total_tokens", "mean"),
		task_count=("total_tokens", "size"),
	)
	.sort_values(["agent_name", "steps"])
	.reset_index(drop=True)
)

# Create the output folder
OUTPUT_FOLDER_PATH.mkdir(parents=True, exist_ok=True)

# Set colors
pastel = sns.color_palette("tab10")
palette = {
	"react-kn-v4.0": pastel[0],
	"modular-full-v4.0": pastel[1],
}

# Create plot
sns.set_style("whitegrid")
fig, ax = plt.subplots(figsize=(12, 6))

sns.scatterplot(
	data=results,
	x="steps",
	y="total_tokens",
	hue="agent_name",
	hue_order=AGENT_ORDER,
	palette=palette,
	alpha=0.30,
	s=60,
	linewidth=0,
	legend=False,
	ax=ax,
)

sns.lineplot(
	data=growth,
	x="steps",
	y="avg_total_tokens",
	hue="agent_name",
	hue_order=AGENT_ORDER,
	palette=palette,
	marker="o",
	linewidth=2.5,
	markersize=6,
	ax=ax,
)

ax.set_title(f"Token Growth by Steps per Task for {MODEL_NAME} (All 10 TextWorld Evals)")
ax.set_xlabel("Steps per task")
ax.set_ylabel("Total tokens")
ax.set_xlim(0, 100)
ax.set_ylim(bottom=0)
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):d}"))
ax.yaxis.set_major_formatter(FuncFormatter(lambda y, pos: f"{int(y):,}"))
ax.legend(title="Agent")

plt.tight_layout()
plt.savefig(OUTPUT_FILE_PATH, bbox_inches="tight")
# plt.show()
plt.close()

print(f"Saved plot to {OUTPUT_FILE_PATH}")


