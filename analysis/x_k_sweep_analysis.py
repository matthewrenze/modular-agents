# K-sweep statistical analysis (modular-kn experiment, Task 7).
# The stats functions (Tee, format_number, format_p_value, bootstrap_mean_difference,
# mcnemar_p_value, wilcoxon_p_value) and the pairing/verification pattern are copied
# verbatim from x_statistical_analysis.py (Option B, decisions.md 2026-08-03) — keep in
# sync with that file until the copies are unified in dev/prod.
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy import stats
import glob


# Set parameters
version = "v6.0"
input_folder_path = f"../data/artifacts/{version}/"
model_name = "gpt-5.4"
bootstrap_resamples = 10_000
bootstrap_seed = 20260504
output_file_path = "../data/k_sweep_analysis.txt"

# The two families' arms in ascending-k order, with the k=1 arm first (the baseline).
react_family = ["react-k1", "react-k5", "react-k10", "react-kn"]
modular_family = ["modular-full", "modular-k5", "modular-k10", "modular-kn"]

# The Holm family: the five new arms, each paired against its own family's k=1 baseline.
# react-kn vs react-k1 is a published v6.0 contrast and is reported descriptively only.
family_contrasts = [
	("react-k1", "react-k5"),
	("react-k1", "react-k10"),
	("modular-full", "modular-k5"),
	("modular-full", "modular-k10"),
	("modular-full", "modular-kn"),
]

# The headline contrast — functional decomposition with history held constant — is a
# single test outside the Holm family (raw p, labeled as such).
headline_contrast = ("react-kn", "modular-kn")


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


# Holm-Bonferroni adjustment (same algorithm as x_statistical_analysis.py, applied
# across a family of contrasts rather than across metrics).
def holm_adjust(raw_p_values):
	sorted_indices = np.argsort(raw_p_values)
	n_tests = len(raw_p_values)
	running_max = 0.0
	holm_p_values = [0.0] * n_tests
	for rank, index in enumerate(sorted_indices):
		adjusted = min(1.0, (n_tests - rank) * raw_p_values[index])
		running_max = max(running_max, adjusted)
		holm_p_values[index] = running_max
	return holm_p_values


# Find all result files at the eval level: <split>/<model>/<agent>/<eval>/
print("Finding result files...")
result_file_paths = glob.glob(f"{input_folder_path}*/*/*/*/*results.csv")
result_file_paths = sorted(path.replace("\\", "/") for path in result_file_paths)
print(f"Found {len(result_file_paths):,} result files")


# Load the data
print("Loading results...")
results = []
for result_file_path in result_file_paths:
	result = pd.read_csv(result_file_path)
	results.append(result)

results = pd.concat(results, ignore_index=True)

# Keep the test split and the analysis model only
results = results[results["split_name"] == "test"].copy()
results = results[results["model_name"] == model_name].copy()

all_arms = react_family + modular_family
results = results[results["agent_name"].isin(all_arms)].copy()
results["success"] = results["success"].astype(str).str.lower().isin(["true", "1"])

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
	"max_steps_hit",
	"total_tokens",
	"total_cost",
	"error",
]].copy()

print(f"Loaded {len(results):,} task rows for {len(all_arms)} arms")


# Verify completeness: 100 episodes per arm, no errors
print("\nVerifying data...")
episode_counts = results.groupby("agent_name").size()
for arm in all_arms:
	count = episode_counts.get(arm, 0)
	print(f"  {arm}: {count} episodes")
	if count != 100:
		raise ValueError(f"{arm} has {count} episodes, expected 100.")

error_rows = results[results["error"].notna() & (results["error"].astype(str).str.strip() != "")]
if len(error_rows) > 0:
	raise ValueError(f"{len(error_rows)} rows carry errors.")
print("  0 error rows")

# Verify pairing: task text identical across all arms per (eval, episode)
task_pairs = results.pivot_table(
	index=["model_name", "eval_name", "episode"],
	columns="agent_name",
	values="task",
	aggfunc="first",
)
task_pairs = task_pairs.dropna()
task_matches = all(
	(task_pairs[arm] == task_pairs[all_arms[0]]).all()
	for arm in all_arms
)
print(f"Paired task groups: {len(task_pairs):,}")
print(f"Task text matches across all arms: {task_matches}")
if not task_matches:
	raise ValueError("Task text does not match across arms.")


# Build the paired table once: one row per episode, one column block per arm
paired = results.pivot_table(
	index=["model_name", "eval_name", "episode"],
	columns="agent_name",
	values=["success", "reward", "reward_per_step", "steps", "total_tokens"],
	aggfunc="first",
).dropna()


# Descriptive curve tables
def print_curve_table(family_label, family):
	print("\n" + "=" * 100)
	print(f"{family_label} — DESCRIPTIVE CURVE (successes /100; totals over 100 episodes)")
	print("=" * 100)
	print(f"{'arm':<14}{'successes':>10}{'steps':>8}{'cap hits':>10}{'tokens':>16}{'cost':>12}")
	for arm in family:
		arm_rows = results[results["agent_name"] == arm]
		successes = int(arm_rows["success"].sum())
		steps = int(arm_rows["steps"].sum())
		cap_hits = int(arm_rows["max_steps_hit"].astype(str).str.lower().isin(["true", "1"]).sum())
		tokens = int(arm_rows["total_tokens"].sum())
		cost = arm_rows["total_cost"].sum()
		print(f"{arm:<14}{successes:>10}{steps:>8}{cap_hits:>10}{tokens:>16,}{cost:>12,.2f}")


print_curve_table("REACT FAMILY", react_family)
print_curve_table("MODULAR FAMILY", modular_family)
print("\nNote: react-kn rebuilds no prompts (append-only conversation) and enjoys a prefix-caching")
print("advantage the finite-k arms do not; dollar comparisons across arms carry that caveat.")
print("Token comparisons are clean.")


# Family contrasts: each new arm vs its family's k=1 baseline, Holm across the family per metric
def run_contrast(arm_a, arm_b):
	success_a = paired[("success", arm_a)].astype(int).to_numpy()
	success_b = paired[("success", arm_b)].astype(int).to_numpy()
	accuracy_p, b_count, c_count = mcnemar_p_value(success_a, success_b)
	accuracy_ci = bootstrap_mean_difference(success_a, success_b)

	contrast = {
		"arm_a": arm_a,
		"arm_b": arm_b,
		"accuracy_a": success_a.mean(),
		"accuracy_b": success_b.mean(),
		"accuracy_ci": accuracy_ci,
		"accuracy_p": accuracy_p,
		"b_count": b_count,
		"c_count": c_count,
	}

	for metric_name in ["steps", "total_tokens"]:
		values_a = paired[(metric_name, arm_a)].astype(float).to_numpy()
		values_b = paired[(metric_name, arm_b)].astype(float).to_numpy()
		contrast[metric_name] = {
			"mean_a": values_a.mean(),
			"mean_b": values_b.mean(),
			"mean_diff": (values_b - values_a).mean(),
			"ci": bootstrap_mean_difference(values_a, values_b),
			"p": wilcoxon_p_value(values_a, values_b),
		}

	return contrast


print("\n" + "=" * 100)
print(f"K-ARM FAMILY CONTRASTS (each new arm vs its family's k=1 baseline; "
	  f"Holm across the {len(family_contrasts)} contrasts per metric)")
print("=" * 100)

contrasts = [run_contrast(arm_a, arm_b) for arm_a, arm_b in family_contrasts]

accuracy_holm = holm_adjust([contrast["accuracy_p"] for contrast in contrasts])
steps_holm = holm_adjust([contrast["steps"]["p"] for contrast in contrasts])
tokens_holm = holm_adjust([contrast["total_tokens"]["p"] for contrast in contrasts])

for contrast, acc_holm, stp_holm, tok_holm in zip(contrasts, accuracy_holm, steps_holm, tokens_holm):
	arm_a, arm_b = contrast["arm_a"], contrast["arm_b"]
	print(f"\n--- {arm_b} vs {arm_a} ---")
	print("accuracy")
	print(f"  {arm_a}: {contrast['accuracy_a']:.2%}   {arm_b}: {contrast['accuracy_b']:.2%}")
	print(f"  difference ({arm_b} - {arm_a}): {contrast['accuracy_b'] - contrast['accuracy_a']:.2%}")
	print(f"  95% paired bootstrap CI: [{contrast['accuracy_ci'][0]:.2%}, {contrast['accuracy_ci'][1]:.2%}]")
	print(f"  exact McNemar p-value: {format_p_value(contrast['accuracy_p'])}   "
		  f"Holm-adjusted: {format_p_value(acc_holm)}")
	print(f"  discordant pairs: {arm_a}-only successes = {contrast['b_count']}, "
		  f"{arm_b}-only successes = {contrast['c_count']}")

	for metric_name, label, holm_value in [
		("steps", "steps-per-task", stp_holm),
		("total_tokens", "tokens-per-task", tok_holm),
	]:
		metric = contrast[metric_name]
		print(f"{label}")
		print(f"  {arm_a}: {format_number(metric['mean_a'])}   {arm_b}: {format_number(metric['mean_b'])}")
		print(f"  mean difference ({arm_b} - {arm_a}): {format_number(metric['mean_diff'])}")
		print(f"  95% paired bootstrap CI: [{format_number(metric['ci'][0])}, {format_number(metric['ci'][1])}]")
		print(f"  Wilcoxon signed-rank p-value: {format_p_value(metric['p'])}   "
			  f"Holm-adjusted: {format_p_value(holm_value)}")


# Headline contrast: modular-kn vs react-kn — a single test outside the Holm family
print("\n" + "=" * 100)
print("HEADLINE CONTRAST (outside the Holm family; raw p): functional decomposition,")
print("history held constant at k=n")
print("=" * 100)

arm_a, arm_b = headline_contrast
contrast = run_contrast(arm_a, arm_b)
print(f"\n--- {arm_b} vs {arm_a} ---")
print("accuracy")
print(f"  {arm_a}: {contrast['accuracy_a']:.2%}   {arm_b}: {contrast['accuracy_b']:.2%}")
print(f"  difference ({arm_b} - {arm_a}): {contrast['accuracy_b'] - contrast['accuracy_a']:.2%}")
print(f"  95% paired bootstrap CI: [{contrast['accuracy_ci'][0]:.2%}, {contrast['accuracy_ci'][1]:.2%}]")
print(f"  exact McNemar p-value (raw): {format_p_value(contrast['accuracy_p'])}")
print(f"  discordant pairs: {arm_a}-only successes = {contrast['b_count']}, "
	  f"{arm_b}-only successes = {contrast['c_count']}")

for metric_name, label in [("steps", "steps-per-task"), ("total_tokens", "tokens-per-task")]:
	metric = contrast[metric_name]
	print(f"{label}")
	print(f"  {arm_a}: {format_number(metric['mean_a'])}   {arm_b}: {format_number(metric['mean_b'])}")
	print(f"  mean difference ({arm_b} - {arm_a}): {format_number(metric['mean_diff'])}")
	print(f"  95% paired bootstrap CI: [{format_number(metric['ci'][0])}, {format_number(metric['ci'][1])}]")
	print(f"  Wilcoxon signed-rank p-value (raw): {format_p_value(metric['p'])}")


# Descriptive reference: the published v6.0 endpoint contrast (not re-tested)
print("\n" + "=" * 100)
print("DESCRIPTIVE REFERENCE (published v6.0 contrasts; not re-tested here)")
print("=" * 100)
for arm_a, arm_b in [("react-k1", "react-kn"), ("react-kn", "modular-full")]:
	success_a = paired[("success", arm_a)].astype(int).to_numpy()
	success_b = paired[("success", arm_b)].astype(int).to_numpy()
	print(f"  {arm_b} vs {arm_a}: {success_a.mean():.0%} -> {success_b.mean():.0%}")

sys.stdout = console_stream
output_file.close()
print(f"Done. Output written to {output_file_path}")
