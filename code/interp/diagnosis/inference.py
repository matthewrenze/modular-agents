import numpy as np
from scipy.stats import norm
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

MODULAR, REACT = "modular-full", "react-kn"

def fit_mixed_logistic(frame) -> dict:
    # Headline inference (protocol section 11): correct ~ architecture + judge,
    # random intercepts for agent model and eval; single-judge frames drop the judge term
    formula = "correct ~ agent_name" + (" + judge" if frame.judge.nunique() > 1 else "")
    model = BinomialBayesMixedGLM.from_formula(
        formula, {"model": "0 + C(model_name)", "eval": "0 + C(eval_name)"},
        frame.assign(correct=frame.correct.astype(int)))
    result = model.fit_vb()
    fixed = {}
    for name, mean, sd in zip(model.fep_names, result.fe_mean, result.fe_sd):
        z = mean / sd
        fixed[name] = {"mean": mean, "sd": sd, "ci_low": mean - 1.96 * sd,
                       "ci_high": mean + 1.96 * sd, "p": 2 * norm.sf(abs(z))}
    return {"fixed": fixed, "summary": str(result.summary())}

def cell_bootstrap_diff(frame, samples: int = 2000, seed: int = 0) -> dict:
    # Assumption-light cross-check: resample (model x eval) cells with replacement,
    # recompute pooled accuracy per architecture and the modular - react difference
    cells = []
    for _, cell in frame.groupby(["model_name", "eval_name"]):
        modular, react = cell[cell.agent_name == MODULAR], cell[cell.agent_name == REACT]
        cells.append((modular.correct.sum(), len(modular), react.correct.sum(), len(react)))
    cells = np.array(cells, dtype=float)
    totals = cells.sum(axis=0)
    modular_rate, react_rate = totals[0] / totals[1], totals[2] / totals[3]

    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(cells), (samples, len(cells)))
    sums = cells[draws].sum(axis=1)
    kept = (sums[:, 1] > 0) & (sums[:, 3] > 0)
    modular_rates, react_rates = sums[kept, 0] / sums[kept, 1], sums[kept, 2] / sums[kept, 3]
    diffs = modular_rates - react_rates
    return {"modular": modular_rate, "react": react_rate, "diff": modular_rate - react_rate,
            "modular_low": np.percentile(modular_rates, 2.5), "modular_high": np.percentile(modular_rates, 97.5),
            "react_low": np.percentile(react_rates, 2.5), "react_high": np.percentile(react_rates, 97.5),
            "diff_low": np.percentile(diffs, 2.5), "diff_high": np.percentile(diffs, 97.5)}
