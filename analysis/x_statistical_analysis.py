from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy import stats


# Set parameters
version = "v6.0"
input_folder_path = f"../data/artifacts/{version}/"
agent_a = "react-kn"
agent_b = "modular-full"
bootstrap_resamples = 10_000
bootstrap_seed = 20260504
output_file_path = "../data/analysis.txt"


class Tee:
	def __init__(self, *streams):
		self.streams = streams

	def write(self, text):
		for stream in self.streams:
			stream.write(text)

	def flush(self):
		for stream in self.streams:
			stream.flush()


output_file = open(output_file_path, "w", encoding="utf-8")
console_stream = sys.stdout
sys.stdout = Tee(console_stream, output_file)


def format_number(value, digits=4):
	if pd.isna(value):
		return "nan"
	return f"{value:.{digits}f}"


def format_p_value(value):
	if pd.isna(value):
		return "nan"
	if value < 0.0001:
		return "<0.0001"
	return f"{value:.4f}"


def bootstrap_mean_difference(values_a, values_b):
	values_a = np.asarray(values_a, dtype=float)
	values_b = np.asarray(values_b, dtype=float)
	differences = values_b - values_a

	if len(differences) == 0:
		return np.nan, np.nan

	if np.allclose(differences, differences[0]):
		return differences[0], differences[0]

	result = stats.bootstrap(
		(values_a, values_b),
		lambda x, y, axis: np.mean(y - x, axis=axis),
		paired=True,
		vectorized=True,
		n_resamples=bootstrap_resamples,
		confidence_level=0.95,
		method="BCa",
		rng=np.random.default_rng(bootstrap_seed),
	)
	return result.confidence_interval.low, result.confidence_interval.high


def mcnemar_p_value(values_a, values_b):
	values_a = np.asarray(values_a, dtype=int)
	values_b = np.asarray(values_b, dtype=int)
	b = int(np.sum((values_a == 1) & (values_b == 0)))
	c = int(np.sum((values_a == 0) & (values_b == 1)))

	if b + c == 0:
		return 1.0, b, c

	p_value = stats.binomtest(min(b, c), n=b + c, p=0.5, alternative="two-sided").pvalue
	return p_value, b, c


def wilcoxon_p_value(values_a, values_b):
	values_a = np.asarray(values_a, dtype=float)
	values_b = np.asarray(values_b, dtype=float)
	differences = values_b - values_a

	if len(differences) == 0:
		return np.nan

	if np.allclose(differences, 0.0):
		return 1.0

	result = stats.wilcoxon(values_b, values_a, alternative="two-sided", zero_method="wilcox")
	return float(result[1])


# Pooled (non-clustered) results. Kept for verification only; do not use for the final analysis.
def print_pooled_results(data, group_label):
	data = data.sort_values(["model_name", "eval_name", "episode", "agent_name"]).copy()
	paired = data.pivot_table(
		index=["model_name", "eval_name", "episode"],
		columns="agent_name",
		values=["success", "reward", "reward_per_step", "steps", "total_tokens"],
		aggfunc="first",
	)

	if paired.empty:
		print(f"\n{group_label}")
		print("No paired data found.")
		return

	agent_names = set(paired.columns.get_level_values(1))
	if agent_a not in agent_names or agent_b not in agent_names:
		print(f"\n{group_label}")
		print("No paired data found.")
		return

	paired = paired.dropna()

	if paired.empty:
		print(f"\n{group_label}")
		print("No paired data found.")
		return

	print("\n" + "=" * 100)
	print(group_label)
	print("=" * 100)
	print(f"Paired tasks: {len(paired):,}")

	success_a = paired[("success", agent_a)].astype(int).to_numpy()
	success_b = paired[("success", agent_b)].astype(int).to_numpy()
	accuracy_a = success_a.mean()
	accuracy_b = success_b.mean()
	accuracy_diff = accuracy_b - accuracy_a
	accuracy_ci_low, accuracy_ci_high = bootstrap_mean_difference(success_a, success_b)
	accuracy_p_value, b_count, c_count = mcnemar_p_value(success_a, success_b)

	print("\naccuracy")
	print(f"  {agent_a}: {accuracy_a:.2%}")
	print(f"  {agent_b}: {accuracy_b:.2%}")
	print(f"  difference ({agent_b} - {agent_a}): {accuracy_diff:.2%}")
	print(f"  95% paired bootstrap CI: [{accuracy_ci_low:.2%}, {accuracy_ci_high:.2%}]")
	print(f"  exact McNemar p-value: {format_p_value(accuracy_p_value)}")
	print(f"  discordant pairs: {agent_a}-only successes = {b_count}, {agent_b}-only successes = {c_count}")

	metrics = [
		("reward", "reward-per-task"),
		("reward_per_step", "reward-per-step"),
		("steps", "steps-per-task"),
		("total_tokens", "tokens-per-task"),
	]

	for metric_name, label in metrics:
		values_a = paired[(metric_name, agent_a)].astype(float).to_numpy()
		values_b = paired[(metric_name, agent_b)].astype(float).to_numpy()
		mean_a = values_a.mean()
		mean_b = values_b.mean()
		mean_diff = (values_b - values_a).mean()
		ci_low, ci_high = bootstrap_mean_difference(values_a, values_b)
		p_value = wilcoxon_p_value(values_a, values_b)

		print(f"\n{label}")
		print(f"  {agent_a}: {format_number(mean_a)}")
		print(f"  {agent_b}: {format_number(mean_b)}")
		print(f"  mean difference ({agent_b} - {agent_a}): {format_number(mean_diff)}")
		print(f"  95% paired bootstrap CI: [{format_number(ci_low)}, {format_number(ci_high)}]")
		print(f"  Wilcoxon signed-rank p-value: {format_p_value(p_value)}")


def print_model_level_results(data, group_label):
	data = data.sort_values(["model_name", "eval_name", "episode", "agent_name"]).copy()
	paired = data.pivot_table(
		index=["model_name", "eval_name", "episode"],
		columns="agent_name",
		values=["success", "reward", "reward_per_step", "steps", "total_tokens"],
		aggfunc="first",
	)

	if paired.empty:
		print(f"\n{group_label}")
		print("No paired data found.")
		return

	agent_names = set(paired.columns.get_level_values(1))
	if agent_a not in agent_names or agent_b not in agent_names:
		print(f"\n{group_label}")
		print("No paired data found.")
		return

	paired = paired.dropna()

	if paired.empty:
		print(f"\n{group_label}")
		print("No paired data found.")
		return

	print("\n" + "=" * 100)
	print(group_label)
	print("=" * 100)
	print(f"Clusters (models): {paired.index.get_level_values('model_name').nunique()}")

	metrics = [
		("success", "accuracy"),
		("reward", "reward-per-task"),
		("reward_per_step", "reward-per-step"),
		("steps", "steps-per-task"),
		("total_tokens", "tokens-per-task"),
	]

	for metric_name, label in metrics:
		differences = paired[(metric_name, agent_b)].astype(float) - paired[(metric_name, agent_a)].astype(float)
		model_means = differences.groupby(level="model_name").mean()
		mean_delta = model_means.mean()
		n_positive = int((model_means > 0).sum())
		n_negative = int((model_means < 0).sum())

		t_p_value = float(stats.ttest_1samp(model_means, 0.0).pvalue)

		n_nonzero = n_positive + n_negative
		if n_nonzero == 0:
			sign_p_value = 1.0
		else:
			sign_p_value = stats.binomtest(min(n_positive, n_negative), n=n_nonzero, p=0.5, alternative="two-sided").pvalue

		print(f"\n{label}")
		for model_name, value in model_means.items():
			print(f"  {model_name}: {format_number(value)}")
		print(f"  mean of per-model differences ({agent_b} - {agent_a}): {format_number(mean_delta)}")
		print(f"  positive: {n_positive}, negative: {n_negative}")
		print(f"  one-sample t-test p-value: {format_p_value(t_p_value)}")
		print(f"  sign test p-value: {format_p_value(sign_p_value)}")


# Find all result files
print("Finding result files...")
result_file_paths = sorted(
	str(path).replace("\\", "/")
	for path in Path(input_folder_path).rglob("*results.csv")
	if path.is_file()
)
print(f"Found {len(result_file_paths):,} result files")


# Load the data
print("Loading results...")
results = []
for result_file_path in result_file_paths:
	result = pd.read_csv(result_file_path)
	results.append(result)

results = pd.concat(results, ignore_index=True)

# Verify the results contain exactly one split
if results["split_name"].nunique() != 1:
	raise ValueError("Results contain both train and test evals.")

results = results[results["agent_name"].isin([agent_a, agent_b])].copy()
results["success"] = results["success"].astype(str).str.lower().isin(["true", "1"])

# Rename models
model_name_mapping = {
    "gemini-3.1-flash-preview": "gemini-3.1-flash",
    "gemini-3.1-pro-preview": "gemini-3.1-pro",
    "kimi-k2.5-turbo": "kimi-k2.5",
    "glm-5-fast": "glm-5"}

results["model_name"] = results["model_name"].replace(model_name_mapping)

# Order models
model_order = [
    "claude-sonnet-4-6",
    # "deepseek-v4",
    "gemini-3.1-pro",
    "gpt-5.2",
    # "gpt-5.4-mini",
    "gpt-5.4",
    "gpt-5.5",
    "glm-5",
    # "glm-5.1",
    "kimi-k2.5",
    # "kimi-k2.6",
    "qwen3.6-plus",
]

# Filter out any models not in the list
results = results[results["model_name"].isin(model_order)]

# Print a list of the unique model names remaining
remaining_models = set(results["model_name"].unique())
print(f"Including {len(remaining_models)} models: ")
for model_name in remaining_models:
	print(f"- {model_name}")


#
if "reward_per_step" not in results.columns:
	results["reward_per_step"] = np.where(results["steps"] > 0, results["reward"] / results["steps"], 0.0)

results = results[[
	"model_name",
	"agent_name",
	"eval_name",
	"episode",
	"task",
	"success",
	"reward",
	"reward_per_step",
	"steps",
	"total_tokens",
]].copy()

print(f"Loaded {len(results):,} task rows for {agent_a} and {agent_b}")


# Verify pairing
task_pairs = results.pivot_table(
	index=["model_name", "eval_name", "episode"],
	columns="agent_name",
	values="task",
	aggfunc="first",
)
task_pairs = task_pairs.dropna()
task_matches = (task_pairs[agent_a] == task_pairs[agent_b]).all()

print(f"Paired task groups: {len(task_pairs):,}")
print(f"Task text matches across pairs: {task_matches}")


# Print model-level (cluster-aware) results overall
print_model_level_results(results, "OVERALL (MODEL-LEVEL / CLUSTER-AWARE)")

# Print pooled results
print_pooled_results(results, "OVERALL (POOLED / NON-CLUSTERED) [DON'T USE]")

sys.stdout = console_stream
output_file.close()
