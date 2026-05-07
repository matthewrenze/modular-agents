# Modular Agents

A research framework for evaluating cognitive architectures for modular LLM agents.

This repository accompanies the paper *Modular LLM Agents: The Effects of Functional and Temporal Decomposition on Performance, Efficiency, and Interpretability*. It contains the agent implementation, evaluation tasks, raw and aggregated results, analysis scripts, and plots needed to reproduce or verify the reported experiments.

# Resources

- [Code](code/) - source code for the agent framework and experiment runner
- [Analysis](analysis/) - analysis scripts used to aggregate results and generate tables/plots
- [Evals](data/evals/) - custom TextWorld evaluation tasks used in the experiments
- [Summaries](data/summaries.csv) - aggregate summaries used for the paper's reported metrics
- [Plots](data/plots/) - generated visualizations used in the paper

# Requirements

- Python 3.x
- Required Python packages listed in `requirements.txt`
- API keys for the LLM providers used in the paper: OpenAI, Anthropic, Google, and Fireworks AI

# Reproducibility

The released assets include the code, evaluation tasks, configuration files, result files, summaries, and plots needed to reproduce or verify the main experimental results.

To reproduce the experiments, install the required dependencies, configure API credentials for the relevant LLM providers, and run the `1_run_evals.py` script from the `code/` directory.

To reproduce the analysis, run the analysis scripts from the `analysis/` directory against `data/summaries.csv`.

Full runtime logs and other diagnostic artifacts are omitted because of their size.
