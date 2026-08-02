import os
import sys
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

sys.path.append("../code")
from models.cost_calculator import CostCalculator


warnings.simplefilter(action="ignore", category=FutureWarning)

# Set parameters
version = "v6.0"
split_name = "test"
model_name = "gpt-5.4"

agent_names = [
    "react-kn",
    "modular-full",
]

eval_names = [
    "tw-long-cook",
    "tw-long-coin",
]

# Steps for the cumulative checkpoint table (rebuttal deliverable)
checkpoint_steps = [50, 100, 150, 200, 250, 300, 350, 400]

# Mean curves are only compared while both agents have at least this many episodes alive
min_alive = 3

# Cost bases: observed = logged implicit-caching split; projected = perfect prefix caching
# (only net-new prompt tokens each step are billed uncached; all repeated content is cached)
cost_bases = ["observed", "projected"]

root_folder_path = f"../data/artifacts/{version}/{split_name}"
output_folder_path = "../data/plots/long-crossover"

os.makedirs(output_folder_path, exist_ok=True)

calculator = CostCalculator()


def save_plot(file_stem, **kwargs):
    for extension in ("pdf", "png"):
        plt.savefig(f"{output_folder_path}/{file_stem}.{extension}", **kwargs)


def fit_polynomial(steps, values, degree):
    coefficients = np.polyfit(steps, values, deg=degree)
    trend_model = np.poly1d(coefficients)
    predicted = trend_model(steps)
    ss_res = ((values - predicted) ** 2).sum()
    ss_tot = ((values - values.mean()) ** 2).sum()
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return trend_model, r_squared


def find_fitted_crossover(react_trend, modular_trend):
    # First positive step where react-kn's fit rises above modular-full's and stays above
    difference = react_trend - modular_trend
    roots = np.roots(difference)
    crossovers = sorted(r.real for r in roots if abs(r.imag) < 1e-9 and r.real > 0 and difference(r.real + 1) > 0)
    return crossovers[0] if crossovers else None


def find_measured_crossover(mean_curves, column):
    # First step where modular-full's mean curve drops to or below react-kn's,
    # restricted to steps where both agents have at least min_alive episodes alive
    react = mean_curves["react-kn"]
    modular = mean_curves["modular-full"]
    compared = react.join(modular, lsuffix="_react", rsuffix="_modular", how="inner")
    compared = compared[(compared["episodes_react"] >= min_alive) & (compared["episodes_modular"] >= min_alive)]
    crossed = compared[compared[f"{column}_modular"] <= compared[f"{column}_react"]]
    last_compared_step = int(compared.index.max())
    if crossed.empty:
        return None, last_compared_step
    return int(crossed.index.min()), last_compared_step


# Load the per-episode results (authoritative success/steps/cost)
result_frames = []

for results_file_path in sorted(Path(root_folder_path).glob(f"{model_name}/*/*/*results.csv")):
    result_frame = pd.read_csv(results_file_path)
    result_frames.append(result_frame)

all_results = pd.concat(result_frames, ignore_index=True)
all_results = all_results[all_results["agent_name"].isin(agent_names) & all_results["eval_name"].isin(eval_names)]

# Load all the details data
details_file_paths = sorted(Path(root_folder_path).glob(f"{model_name}/*/*/*/*details.csv"))
frames = []

for details_file_path in details_file_paths:
    file_name_parts = details_file_path.stem.split(" - ")
    agent_name = file_name_parts[3]
    eval_name = file_name_parts[4]
    episode_id = int(file_name_parts[5].replace("episode-", ""))
    if agent_name not in agent_names or eval_name not in eval_names:
        continue

    frame = pd.read_csv(details_file_path)
    frame["agent_name"] = agent_name
    frame["eval_name"] = eval_name
    frame["episode_id"] = episode_id
    frames.append(frame)

all_details = pd.concat(frames, ignore_index=True)
all_details = all_details.sort_values(["eval_name", "agent_name", "episode_id", "step_id"])

print(f"Loaded {len(all_details):,} steps from {len(frames)} episodes.")

# Compute per-step prompt tokens and observed cost from the logged caching split
all_details["prompt_tokens"] = all_details["cached_tokens"] + all_details["input_tokens"]
all_details["cost_observed"] = all_details.apply(
    lambda row: calculator.get_input_cost(model_name, row.cached_tokens, row.input_tokens)
    + calculator.get_output_cost(model_name, row.reasoning_tokens, row.output_tokens), axis=1)

# Compute the projected explicit-caching cost: only net-new prompt tokens are billed uncached
episode_groups = all_details.groupby(["eval_name", "agent_name", "episode_id"])
all_details["new_prompt_tokens"] = episode_groups["prompt_tokens"].diff().clip(lower=0)
all_details["new_prompt_tokens"] = all_details["new_prompt_tokens"].fillna(all_details["prompt_tokens"])
all_details["repeated_prompt_tokens"] = all_details["prompt_tokens"] - all_details["new_prompt_tokens"]
all_details["cost_projected"] = all_details.apply(
    lambda row: calculator.get_input_cost(model_name, row.repeated_prompt_tokens, row.new_prompt_tokens)
    + calculator.get_output_cost(model_name, row.reasoning_tokens, row.output_tokens), axis=1)

# Compute cumulative curves per episode
episode_groups = all_details.groupby(["eval_name", "agent_name", "episode_id"])
all_details["cumulative_tokens"] = episode_groups["total_tokens"].cumsum()
all_details["cumulative_cost_observed"] = episode_groups["cost_observed"].cumsum()
all_details["cumulative_cost_projected"] = episode_groups["cost_projected"].cumsum()

# Analyze each eval
for eval_name in eval_names:
    print(f"\n{'=' * 72}\n=== {eval_name} ===\n{'=' * 72}")
    eval_details = all_details[all_details["eval_name"] == eval_name]

    # Report the per-cell episode outcomes
    print("\n--- Episode outcomes ---")
    for agent_name in agent_names:
        episodes = all_results[(all_results["eval_name"] == eval_name) & (all_results["agent_name"] == agent_name)]
        successes = int(episodes["success"].sum())
        cached_share = episodes["cached_tokens"].sum() / (episodes["cached_tokens"].sum() + episodes["input_tokens"].sum())
        print(f"{agent_name}: {successes}/{len(episodes)} successes | "
              f"steps min/median/max = {episodes.steps.min()}/{episodes.steps.median():.0f}/{episodes.steps.max()} | "
              f"cost/episode mean ${episodes.total_cost.mean():.2f} (total ${episodes.total_cost.sum():.2f}) | "
              f"cached share {cached_share:.1%}")

    # Fit the marginal token and cost trends (pooled across episodes, linear)
    print("\n--- Fitted marginal trends (pooled across episodes, linear) ---")
    marginal_trends = {}
    cost_trends = {basis: {} for basis in cost_bases}
    for agent_name in agent_names:
        agent_details = eval_details[eval_details["agent_name"] == agent_name]
        steps = agent_details["step_id"].to_numpy(dtype=float)
        trend_model, r_squared = fit_polynomial(steps, agent_details["total_tokens"].to_numpy(dtype=float), 1)
        marginal_trends[agent_name] = trend_model
        print(f"{agent_name}: tokens/step = {trend_model[1]:,.1f} x step + {trend_model[0]:,.0f} (R2 = {r_squared:.3f})")
        for basis in cost_bases:
            trend_model, r_squared = fit_polynomial(steps, agent_details[f"cost_{basis}"].to_numpy(dtype=float) * 100, 1)
            cost_trends[basis][agent_name] = trend_model
            print(f"  cost/step ({basis}): cents/step = {trend_model[1]:.4f} x step + {trend_model[0]:.2f} (R2 = {r_squared:.3f})")

    # Fit the cumulative trends (pooled across episodes, quadratic — matches 7_analyze_token_growth.py)
    print("\n--- Fitted cumulative trends (pooled across episodes, quadratic) ---")
    cumulative_trends = {}
    cumulative_cost_trends = {basis: {} for basis in cost_bases}
    for agent_name in agent_names:
        agent_details = eval_details[eval_details["agent_name"] == agent_name]
        steps = agent_details["step_id"].to_numpy(dtype=float)
        trend_model, r_squared = fit_polynomial(steps, agent_details["cumulative_tokens"].to_numpy(dtype=float), 2)
        cumulative_trends[agent_name] = trend_model
        print(f"{agent_name}: cumulative tokens = {trend_model[2]:,.1f} x step^2 + {trend_model[1]:,.0f} x step + {trend_model[0]:,.0f} (R2 = {r_squared:.3f})")
        for basis in cost_bases:
            trend_model, r_squared = fit_polynomial(steps, agent_details[f"cumulative_cost_{basis}"].to_numpy(dtype=float), 2)
            cumulative_cost_trends[basis][agent_name] = trend_model

    # Compute the mean curves across alive episodes with 95% CIs
    mean_curves = {}
    for agent_name in agent_names:
        agent_details = eval_details[eval_details["agent_name"] == agent_name]
        curve_columns = ["total_tokens", "cumulative_tokens", "cumulative_cost_observed", "cumulative_cost_projected"]
        curves = agent_details.groupby("step_id")[curve_columns].agg(["mean", "sem", "count"])
        curves.columns = [f"{column}_{stat}" for column, stat in curves.columns]
        curves = curves.rename(columns={"total_tokens_count": "episodes"})
        mean_curves[agent_name] = curves

    # Report the measured and fitted crossovers on all bases
    print("\n--- Crossovers (react-kn exceeds modular-full) ---")
    max_observed_step = int(eval_details["step_id"].max())
    fitted_marginal = find_fitted_crossover(marginal_trends["react-kn"], marginal_trends["modular-full"])
    fitted_marginal_text = f"step {fitted_marginal:,.0f}" if fitted_marginal else "none"
    print(f"marginal tokens: fitted {fitted_marginal_text} (last observed step: {max_observed_step})")

    crossover_specs = [("cumulative_tokens_mean", "cumulative tokens", cumulative_trends)] + [
        (f"cumulative_cost_{basis}_mean", f"cumulative cost ({basis} caching)", cumulative_cost_trends[basis])
        for basis in cost_bases
    ]
    for column, label, trends in crossover_specs:
        measured_step, last_compared_step = find_measured_crossover(mean_curves, column)
        measured_text = f"step {measured_step}" if measured_step else f"none within {last_compared_step} compared steps"
        fitted_step = find_fitted_crossover(trends["react-kn"], trends["modular-full"])
        fitted_text = f"step {fitted_step:,.0f}" if fitted_step else "none"
        print(f"{label}: measured {measured_text} (>= {min_alive} episodes alive per arm) | fit projects {fitted_text}")

    # Build the cumulative checkpoint table (mean across episodes alive at each step)
    print("\n--- Cumulative checkpoints (mean across alive episodes) ---")
    checkpoint_rows = []
    for checkpoint_step in checkpoint_steps:
        row = {"step": checkpoint_step}
        for agent_name, prefix in [("react-kn", "react"), ("modular-full", "modular")]:
            curves = mean_curves[agent_name]
            if checkpoint_step not in curves.index:
                continue
            checkpoint = curves.loc[checkpoint_step]
            row[f"{prefix}_n"] = int(checkpoint["episodes"])
            row[f"{prefix}_Mtok"] = checkpoint["cumulative_tokens_mean"] / 1e6
            row[f"{prefix}_$obs"] = checkpoint["cumulative_cost_observed_mean"]
            row[f"{prefix}_$proj"] = checkpoint["cumulative_cost_projected_mean"]
        if len(row) > 1:
            checkpoint_rows.append(row)
    checkpoint_table = pd.DataFrame(checkpoint_rows)
    for column in checkpoint_table.columns:
        if column == "step" or column.endswith("_n"):
            checkpoint_table[column] = checkpoint_table[column].astype("Int64")
    checkpoint_table.to_csv(f"{output_folder_path}/checkpoints-{eval_name}.csv", index=False)
    checkpoint_markdown = checkpoint_table.to_markdown(index=False, floatfmt=",.2f")
    with open(f"{output_folder_path}/checkpoints-{eval_name}.md", "w", encoding="utf-8") as markdown_file:
        markdown_file.write(checkpoint_markdown)
    print(checkpoint_markdown)

    # Plot the marginal and cumulative curves with 95% CI bands
    plot_specs = [
        ("total_tokens", "Tokens per Step", "marginal-tokens", 1),
        ("cumulative_tokens", "Cumulative Tokens (millions)", "cumulative-tokens", 1e6),
        ("cumulative_cost_observed", "Cumulative Cost (USD, observed caching)", "cumulative-cost-observed", 1),
        ("cumulative_cost_projected", "Cumulative Cost (USD, projected explicit caching)", "cumulative-cost-projected", 1),
    ]
    for column, y_label, file_label, scale in plot_specs:
        plt.figure(figsize=(10, 6))
        for agent_name in agent_names:
            curves = mean_curves[agent_name]
            mean = curves[f"{column}_mean"] / scale
            interval = 1.96 * curves[f"{column}_sem"] / scale
            plt.plot(curves.index, mean, label=agent_name)
            plt.fill_between(curves.index, mean - interval, mean + interval, alpha=0.2)
        plt.title(f"{y_label} - {eval_name} - {model_name}")
        plt.xlabel("Step")
        plt.ylabel(y_label)
        plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.2f}" if scale == 1 and "Cost" in y_label else f"{x:,.0f}"))
        plt.legend(title="Agent")
        plt.tight_layout()
        save_plot(f"{file_label}-{eval_name}", dpi=300)
        plt.close()

print(f"\nSaved checkpoint tables and plots to {output_folder_path}")
