import os
import warnings

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.container import BarContainer
from matplotlib.ticker import PercentFormatter


warnings.simplefilter(action="ignore", category=FutureWarning)

# Set parameters
version = "v6.0"
input_file_path = "../data/summaries.csv"
output_folder_path = "../data/plots/token-caching"
output_table_file_stem = os.path.join(output_folder_path, "token-caching-efficiency-by-model-and-agent")
output_plot_file_stem = os.path.join(output_folder_path, "token-caching-efficiency-by-model-and-agent")

agent_order = [
    "react-kn",
    "modular-full",
]

model_name_mapping = {
    "gemini-3.1-flash-preview": "gemini-3.1-flash",
    "gemini-3.1-pro-preview": "gemini-3.1-pro",
    "kimi-k2.5-turbo": "kimi-k2.5",
    "glm-5-fast": "glm-5",
}

model_order = [
    # "claude-sonnet-4-6",
    # "gemini-3.1-pro",
    # "gpt-5.2",
    "gpt-5.4",
    # "gpt-5.5",
    # "glm-5",
    # "kimi-k2.5",
    # "qwen3.6-plus",
]

pastel = sns.color_palette("tab10")
palette = {
    name:
        pastel[7] if name.startswith("react") else
        pastel[0] if name.startswith("modular-full") else
        pastel[7]
    for name in agent_order
}

required_columns = {
    "model_name",
    "agent_name",
    "eval_name",
    "episodes",
    "cached_tokens",
    "input_tokens",
}


os.makedirs(output_folder_path, exist_ok=True)


def save_plot(file_stem: str, **kwargs):
    for extension in ("pdf", "png"):
        plt.savefig(f"{file_stem}.{extension}", **kwargs)


def show_plot_if_interactive():
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="FigureCanvasAgg is non-interactive, and thus cannot be shown",
            category=UserWarning,
        )
        plt.show()


# Load the data
summaries = pd.read_csv(input_file_path)

missing_columns = required_columns.difference(summaries.columns)
if missing_columns:
    missing_columns_text = ", ".join(sorted(missing_columns))
    raise ValueError(f"Missing required columns in summaries.csv: {missing_columns_text}")

# Filter rows
summaries = summaries[summaries["version"] == version].copy()
summaries = summaries[summaries["eval_name"].str.startswith("tw-", na=False)].copy()
summaries = summaries[summaries["agent_name"].isin(agent_order)].copy()
summaries = summaries[~summaries["model_name"].str.startswith("deepseek-v4", na=False)].copy()
summaries["model_name"] = summaries["model_name"].replace(model_name_mapping)

# Aggregate prompt token caching stats
summaries = summaries.groupby(["model_name", "agent_name"], as_index=False).agg({
    "episodes": "sum",
    "cached_tokens": "sum",
    "input_tokens": "sum",
})

summaries["prompt_tokens"] = summaries["cached_tokens"] + summaries["input_tokens"]
summaries["pct_cached"] = summaries["cached_tokens"].div(summaries["prompt_tokens"]).fillna(0.0)
summaries["pct_uncached"] = summaries["input_tokens"].div(summaries["prompt_tokens"]).fillna(0.0)
summaries["avg_prompt_tokens_per_episode"] = summaries["prompt_tokens"].div(summaries["episodes"]).fillna(0.0)
summaries["avg_cached_tokens_per_episode"] = summaries["cached_tokens"].div(summaries["episodes"]).fillna(0.0)
summaries["avg_uncached_tokens_per_episode"] = summaries["input_tokens"].div(summaries["episodes"]).fillna(0.0)

summaries = summaries[summaries["model_name"].isin(model_order)].copy()
summaries["model_name"] = pd.Categorical(
    summaries["model_name"],
    categories=model_order,
    ordered=True,
)
summaries["agent_name"] = pd.Categorical(
    summaries["agent_name"],
    categories=agent_order,
    ordered=True,
)
summaries = summaries.sort_values(["agent_name", "model_name"]).reset_index(drop=True)

# Build an overall summary by agent to make the winner easy to inspect
agent_summary = summaries.groupby("agent_name", as_index=False).agg({
    "episodes": "sum",
    "cached_tokens": "sum",
    "input_tokens": "sum",
    "prompt_tokens": "sum",
})
agent_summary["pct_cached"] = agent_summary["cached_tokens"].div(agent_summary["prompt_tokens"]).fillna(0.0)
agent_summary["pct_uncached"] = agent_summary["input_tokens"].div(agent_summary["prompt_tokens"]).fillna(0.0)
agent_summary["avg_prompt_tokens_per_episode"] = agent_summary["prompt_tokens"].div(agent_summary["episodes"]).fillna(0.0)
agent_summary["avg_cached_tokens_per_episode"] = agent_summary["cached_tokens"].div(agent_summary["episodes"]).fillna(0.0)
agent_summary["avg_uncached_tokens_per_episode"] = agent_summary["input_tokens"].div(agent_summary["episodes"]).fillna(0.0)
agent_summary.insert(0, "model_name", "ALL")
agent_summary = agent_summary[[
    "model_name",
    "agent_name",
    "episodes",
    "cached_tokens",
    "input_tokens",
    "prompt_tokens",
    "pct_cached",
    "pct_uncached",
    "avg_cached_tokens_per_episode",
    "avg_uncached_tokens_per_episode",
    "avg_prompt_tokens_per_episode",
]]

report_table = pd.concat([
    summaries[[
        "model_name",
        "agent_name",
        "episodes",
        "cached_tokens",
        "input_tokens",
        "prompt_tokens",
        "pct_cached",
        "pct_uncached",
        "avg_cached_tokens_per_episode",
        "avg_uncached_tokens_per_episode",
        "avg_prompt_tokens_per_episode",
    ]],
    agent_summary,
], ignore_index=True)

report_table["model_sort"] = report_table["model_name"].astype(str).map({name: i for i, name in enumerate(model_order)})
report_table["model_sort"] = report_table["model_sort"].fillna(len(model_order))
report_table["agent_sort"] = report_table["agent_name"].astype(str).map({name: i for i, name in enumerate(agent_order)})
report_table = report_table.sort_values(["model_sort", "agent_sort"]).drop(columns=["model_sort", "agent_sort"]).reset_index(drop=True)

# Save a machine-readable table and a markdown table for quick inspection
report_table.to_csv(f"{output_table_file_stem}.csv", index=False)
report_table_markdown = report_table.copy()
for column in ["pct_cached", "pct_uncached"]:
    report_table_markdown[column] = report_table_markdown[column].map(lambda x: f"{x:.1%}")
for column in [
    "cached_tokens",
    "input_tokens",
    "prompt_tokens",
    "avg_cached_tokens_per_episode",
    "avg_uncached_tokens_per_episode",
    "avg_prompt_tokens_per_episode",
]:
    report_table_markdown[column] = report_table_markdown[column].map(lambda x: f"{x:,.0f}")
markdown_table = report_table_markdown.to_markdown(index=False)
with open(f"{output_table_file_stem}.md", "w", encoding="utf-8") as markdown_file:
    markdown_file.write(markdown_table)

print("Token caching efficiency table:")
print(markdown_table)
print()

best_agent = agent_summary.sort_values("pct_cached", ascending=False).iloc[0]
print(
    "Overall best token caching efficiency: "
    f"{best_agent['agent_name']} ({best_agent['pct_cached']:.1%} cached prompt tokens)."
)
print()

# Plot cached-token efficiency in the same grouped-bar style as 2_analyze_by_model_and_agent.py
sns.set_theme(
    style="whitegrid",
    font="sans-serif",
    font_scale=1.25,
)
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    x="model_name",
    y="pct_cached",
    hue="agent_name",
    data=summaries,
    palette=palette,
)
plt.title("Token Caching Efficiency by Model and Agent")
plt.xlabel("Model")
plt.ylabel("Cached prompt tokens")
plt.ylim(0.0, 1.0)
plt.xticks(rotation=15, ha="right")
plt.subplots_adjust(bottom=0.22)
plt.legend(title="Agent", loc="upper left")
ax.yaxis.set_major_formatter(PercentFormatter(1.0))

for container, agent_name in zip([c for c in ax.containers if isinstance(c, BarContainer)], agent_order):
    values = summaries[summaries["agent_name"] == agent_name].set_index("model_name")["pct_cached"]
    labels = ["" if pd.isna(values.get(model_name)) else f"{values.get(model_name):.0%}" for model_name in model_order]
    ax.bar_label(container, labels=labels, padding=3, fontsize=9)

plt.tight_layout()
save_plot(output_plot_file_stem, bbox_inches="tight", dpi=300)
show_plot_if_interactive()
plt.close()

