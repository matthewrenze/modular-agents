from interp.plan.action_matcher import ActionMatcher
from interp.plan.plan_parser import PlanParser
from interp.plan.plan_scorer import PlanScorer

PLAN_STEP_1 = "- [ ] Open the antique trunk\n- [ ] Take the old key\n- [ ] Go east\n"
PLAN_STEP_2 = "- [x] Open the antique trunk\n- [ ] Take the old key\n- [ ] Go east\n"
PLAN_DONE = "- [x] Open the antique trunk\n- [x] Take the old key\n- [x] Go east\n"

def make_scorer():
    return PlanScorer(PlanParser(), ActionMatcher())

class TestScoreAgreement:

    def test_counts_exact_and_fuzzy_matches_on_the_current_open_leaf(self):
        steps = [(PLAN_STEP_1, "open antique trunk"),
                 (PLAN_STEP_2, "take the old key from the antique trunk")]
        scores = make_scorer().score_agreement(steps)
        assert scores["n_steps"] == 2
        assert scores["n_current_exact"] == 1
        assert scores["n_current_fuzzy"] == 1
        assert scores["n_mismatch"] == 0

    def test_action_matching_a_later_open_leaf_counts_as_any_open(self):
        scores = make_scorer().score_agreement([(PLAN_STEP_2, "go east")])
        assert scores["n_any_open"] == 1
        assert scores["n_mismatch"] == 0

    def test_unmatched_action_is_a_mismatch_with_audit_row(self):
        scores = make_scorer().score_agreement([(PLAN_STEP_1, "look")])
        assert scores["n_mismatch"] == 1
        assert scores["mismatches"] == [("look", "Open the antique trunk")]

    def test_completed_plan_and_missing_plan_are_counted_separately(self):
        scores = make_scorer().score_agreement([(PLAN_DONE, "look"), ("", "look")])
        assert scores["n_no_open"] == 1
        assert scores["n_no_plan"] == 1
        assert scores["n_mismatch"] == 0

    def test_unparseable_plan_is_not_counted_as_complete(self):
        scores = make_scorer().score_agreement([("prose dump, not a checklist", "look")])
        assert scores["n_unparseable"] == 1
        assert scores["n_no_open"] == 0

class TestScoreCorrectness:

    def test_lcs_against_solution_commands(self):
        solution = ["open antique trunk", "take old key", "go east"]
        scores = make_scorer().score_correctness(PLAN_STEP_1, solution)
        assert scores == {"lcs": 3, "n_leaves": 3, "n_solution": 3}

    def test_out_of_order_and_extra_items_reduce_lcs(self):
        plan = "- [ ] Go east\n- [ ] Examine the cookbook\n- [ ] Open the antique trunk\n"
        solution = ["open antique trunk", "go east"]
        scores = make_scorer().score_correctness(plan, solution)
        assert scores == {"lcs": 1, "n_leaves": 3, "n_solution": 2}

    def test_lcs_uses_fuzzy_matching(self):
        plan = "- [ ] Go east to the garden\n"
        scores = make_scorer().score_correctness(plan, ["go east"])
        assert scores["lcs"] == 1

class TestScoreHygiene:

    def test_counts_lines_invalid_lines_and_leaves(self):
        scores = make_scorer().score_hygiene("- [x] Go east\nstray text\n- [ ] Go west\n")
        assert scores["n_lines"] == 3
        assert scores["n_invalid_lines"] == 1
        assert scores["n_leaves"] == 2

    def test_counts_duplicate_leaves_and_max_run(self):
        plan = "- [ ] Go east\n- [ ] Go east\n- [ ] Go east\n- [ ] Go west\n- [ ] Go east\n"
        scores = make_scorer().score_hygiene(plan)
        assert scores["n_duplicate_leaves"] == 3
        assert scores["max_leaf_run"] == 3
