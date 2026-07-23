import pytest
from interp.diagnosis.ensemble import majority, step_window, pairwise_rate, fleiss_kappa

class TestMajority:

    def test_unanimous(self):
        assert majority(["a", "a", "a"]) == "a"

    def test_two_of_three(self):
        assert majority(["a", "b", "a"]) == "a"

    def test_no_majority(self):
        assert majority(["a", "b", "c"]) is None

    def test_step_votes(self):
        assert majority([41, 39, 41]) == 41

    def test_null_majority_means_no_ground_truth(self):
        assert majority([None, None, 41]) is None

    def test_two_votes(self):
        assert majority(["a", "a"]) == "a"

class TestStepWindow:

    def test_window_spans_non_null_votes(self):
        assert step_window([39, 41, None]) == (39, 41)

    def test_all_null_has_no_window(self):
        assert step_window([None, None, None]) is None

class TestPairwiseRate:

    def test_rate(self):
        assert pairwise_rate(["a", "b", "c"], ["a", "b", "d"]) == pytest.approx(2 / 3)

class TestFleissKappa:

    def test_perfect_agreement(self):
        assert fleiss_kappa([["a", "a", "a"], ["b", "b", "b"]]) == pytest.approx(1.0)

    def test_disagreement_below_perfect(self):
        assert fleiss_kappa([["a", "b", "c"], ["b", "c", "a"], ["a", "a", "b"]]) < 0.5

    def test_null_votes_are_a_category(self):
        assert fleiss_kappa([[None, None, 3], [3, 3, 3]]) < 1.0
