import numpy as np
import pandas as pd
import pytest
from interp.diagnosis.inference import fit_mixed_logistic, cell_bootstrap_diff

def make_frame():
    # Synthetic grid with a strong known architecture effect (react more diagnosable)
    rng = np.random.default_rng(0)
    n = 400
    frame = pd.DataFrame({
        "agent_name": rng.choice(["modular-full", "react-kn"], n),
        "judge": rng.choice(["gpt", "fable", "gemini"], n),
        "model_name": rng.choice([f"m{i}" for i in range(5)], n),
        "eval_name": rng.choice([f"e{i}" for i in range(5)], n)})
    logit = -0.5 + 1.5 * (frame.agent_name == "react-kn")
    frame["correct"] = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
    return frame

class TestFitMixedLogistic:

    def test_recovers_architecture_effect(self):
        result = fit_mixed_logistic(make_frame())
        effect = result["fixed"]["agent_name[T.react-kn]"]
        assert effect["mean"] > 0.5
        assert effect["ci_low"] > 0.0
        assert effect["p"] < 0.05

    def test_reports_all_fixed_effects_and_summary(self):
        result = fit_mixed_logistic(make_frame())
        assert "Intercept" in result["fixed"]
        assert "model" in result["summary"] and "eval" in result["summary"]

class TestCellBootstrapDiff:

    def make_frame(self):
        # Two cells; modular 1/4 correct, react 3/4 correct
        return pd.DataFrame({
            "model_name": ["m1"] * 4 + ["m2"] * 4,
            "eval_name": ["e1"] * 8,
            "agent_name": ["modular-full", "modular-full", "react-kn", "react-kn"] * 2,
            "correct": [True, False, True, True, False, False, True, False]})

    def test_point_estimates(self):
        result = cell_bootstrap_diff(self.make_frame(), samples=200, seed=0)
        assert result["modular"] == pytest.approx(0.25)
        assert result["react"] == pytest.approx(0.75)
        assert result["diff"] == pytest.approx(-0.5)
        assert result["diff_low"] <= result["diff"] <= result["diff_high"]

    def test_seed_reproducible(self):
        first = cell_bootstrap_diff(self.make_frame(), samples=200, seed=0)
        second = cell_bootstrap_diff(self.make_frame(), samples=200, seed=0)
        assert first == second
