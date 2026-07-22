import pytest
from interp.diagnosis.scoring import (score_class, score_step, cohens_kappa, chance_floors,
                                      brier_score, reliability_bins)

class TestScoreClass:

    def test_strict_match(self):
        assert score_class("a", "b", "a") == {"strict": True, "lenient": True}

    def test_lenient_via_secondary(self):
        assert score_class("b", "a", "a") == {"strict": False, "lenient": True}

    def test_miss(self):
        assert score_class("b", "c", "a") == {"strict": False, "lenient": False}

    def test_null_secondary(self):
        assert score_class("b", None, "a") == {"strict": False, "lenient": False}

class TestScoreStep:

    def test_exact(self):
        scores = score_step(41, 41, (39, 43))
        assert scores == {"step_exact": True, "step_window2": True, "step_dynamic": True}

    def test_within_fixed_window_only(self):
        scores = score_step(43, 41, (40, 42))
        assert scores == {"step_exact": False, "step_window2": True, "step_dynamic": False}

    def test_within_dynamic_window_only(self):
        scores = score_step(45, 41, (40, 45))
        assert scores == {"step_exact": False, "step_window2": False, "step_dynamic": True}

    def test_null_judge_step_scores_false(self):
        scores = score_step(None, 41, (40, 42))
        assert scores == {"step_exact": False, "step_window2": False, "step_dynamic": False}

class TestCohensKappa:

    def test_perfect(self):
        assert cohens_kappa(["a", "b"], ["a", "b"]) == pytest.approx(1.0)

    def test_hand_example(self):
        # po = 3/4; pe = 0.5 * 0.25 + 0.5 * 0.75 = 0.5; kappa = 0.5
        assert cohens_kappa(["a", "a", "b", "b"], ["a", "b", "b", "b"]) == pytest.approx(0.5)

class TestChanceFloors:

    def test_hand_example(self):
        # Family 1: [a, a, b] -> majority 2/3, matched 5/9; family 2: [b] -> 1, 1
        floors = chance_floors(["a", "a", "b", "b"], ["f1", "f1", "f1", "f2"])
        assert floors["majority"] == pytest.approx(3 / 4)
        assert floors["matched_random"] == pytest.approx((3 * 5 / 9 + 1) / 4)

    def test_single_family_is_unconditional(self):
        floors = chance_floors(["a", "a", "b"], ["all", "all", "all"])
        assert floors["majority"] == pytest.approx(2 / 3)

class TestBrierScore:

    def test_hand_example(self):
        assert brier_score([1.0, 0.5], [True, False]) == pytest.approx(0.125)

class TestReliabilityBins:

    def test_bins(self):
        rows = reliability_bins([0.1, 0.9, 0.95], [False, True, False], n_bins=2)
        assert len(rows) == 2
        assert rows[0] == {"low": 0.0, "high": 0.5, "n": 1, "mean_confidence": pytest.approx(0.1),
                           "accuracy": pytest.approx(0.0)}
        assert rows[1]["n"] == 2
        assert rows[1]["accuracy"] == pytest.approx(0.5)

    def test_confidence_of_one_lands_in_top_bin(self):
        rows = reliability_bins([1.0], [True], n_bins=5)
        assert rows[0]["low"] == pytest.approx(0.8)
        assert rows[0]["n"] == 1
