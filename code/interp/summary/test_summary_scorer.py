from interp.plan.action_matcher import ActionMatcher
from interp.summary.summary_parser import SummaryParser
from interp.summary.summary_scorer import SummaryScorer

def make_diff(**overrides):
    diff = {"step_id": 2, "prev_action": "go east", "location_from": "Bedroom", "location_to": "Kitchen",
            "inventory_from": "You are carrying: an old key.", "inventory_to": "You are carrying: an old key.",
            "score_from": 0, "score_to": 0, "feedback": ""}
    diff.update(overrides)
    return diff

def score(steps):
    return SummaryScorer(SummaryParser(), ActionMatcher()).score(steps)

class TestEcho:

    def test_exact_and_fuzzy_echo_matches(self):
        scores = score([("go east → location = Kitchen", make_diff()),
                        ("go east → location = Kitchen", make_diff(prev_action="go east\ngo east"))])
        assert scores["echo_exact"] == 1
        assert scores["echo_fuzzy"] == 1

    def test_echo_disagreeing_with_the_action_is_a_mismatch_with_audit_row(self):
        scores = score([("go west → location = Kitchen", make_diff())])
        assert scores["echo_mismatch"] == 1
        assert scores["echo_mismatches"] == [("go west", "go east")]

    def test_the_start_step_expects_a_start_echo(self):
        scores = score([("start → location = Bedroom", make_diff(
            prev_action="", location_from="", location_to="Bedroom"))])
        assert scores["echo_exact"] == 1

class TestLocation:

    def test_true_location_claim_on_a_move_counts_precision_and_recall(self):
        scores = score([("go east → location = kitchen", make_diff())])
        assert scores["loc_tp"] == 1
        assert scores["loc_changes"] == 1
        assert scores["loc_hits"] == 1

    def test_false_location_claim_is_an_fp_and_the_move_is_missed(self):
        scores = score([("go east → location = attic", make_diff())])
        assert scores["loc_fp"] == 1
        assert scores["loc_hits"] == 0
        assert scores["fp_claims"] == [("location", "attic", "Kitchen")]
        assert scores["missed_changes"] == [("location", "Kitchen")]

    def test_unclaimed_move_is_a_missed_change(self):
        scores = score([("go east → score += 1", make_diff(score_to=1))])
        assert scores["loc_changes"] == 1
        assert scores["loc_hits"] == 0

    def test_true_claim_without_a_move_is_redundant_but_not_false(self):
        scores = score([("look → location = Bedroom", make_diff(
            prev_action="look", location_to="Bedroom"))])
        assert scores["loc_tp"] == 1
        assert scores["loc_redundant"] == 1
        assert scores["loc_changes"] == 0

class TestInventory:

    def test_true_add_and_remove_claims_count_precision_and_recall(self):
        diff = make_diff(prev_action="take knife", location_from="Kitchen",
                         inventory_from="You are carrying: an old key.",
                         inventory_to="You are carrying: an old key and a knife.")
        scores = score([("take knife → inventory += knife", diff)])
        assert scores["inv_tp"] == 1
        assert scores["inv_changes"] == 1
        assert scores["inv_hits"] == 1

    def test_false_inventory_claim_is_an_fp(self):
        scores = score([("go east → inventory += knife", make_diff())])
        assert scores["inv_fp"] == 1
        assert scores["inv_changes"] == 0

    def test_unclaimed_removal_is_a_missed_change(self):
        diff = make_diff(prev_action="drop old key", location_from="Kitchen",
                         inventory_to="You are carrying nothing.")
        scores = score([("drop old key → old key = dropped", diff)])
        assert scores["inv_changes"] == 1
        assert scores["inv_hits"] == 0
        assert scores["missed_changes"] == [("inventory_removed", "old key")]

    def test_meal_preparation_changes_are_also_counted_in_the_meal_subset(self):
        diff = make_diff(prev_action="prepare meal", location_from="Kitchen",
                         inventory_from="You are carrying: a white onion and a yellow potato.",
                         inventory_to="You are carrying: a meal.")
        scores = score([("prepare meal → inventory += meal; score += 1", diff)])
        assert scores["inv_changes"] == 3
        assert scores["inv_hits"] == 1
        assert scores["inv_meal_changes"] == 3
        assert scores["inv_meal_hits"] == 1

class TestScore:

    def test_correct_and_wrong_score_deltas(self):
        scores = score([("go east → location = kitchen; score += 1", make_diff(score_to=1)),
                        ("go east → location = kitchen; score += 2", make_diff(score_to=1))])
        assert scores["score_tp"] == 1
        assert scores["score_fp"] == 1
        assert scores["score_changes"] == 2
        assert scores["score_hits"] == 1

    def test_unclaimed_score_change_is_a_missed_change(self):
        scores = score([("go east → location = kitchen", make_diff(score_to=1))])
        assert scores["score_changes"] == 1
        assert scores["score_hits"] == 0

class TestStepHandling:

    def test_the_start_step_skips_the_inventory_and_score_channels(self):
        scores = score([("start → location = Bedroom", make_diff(
            prev_action="", location_from="", location_to="Bedroom",
            inventory_from="", inventory_to="You are carrying: a cookbook."))])
        assert scores["inv_changes"] == 0
        assert scores["score_changes"] == 0
        assert scores["loc_changes"] == 1

    def test_unparseable_summary_still_counts_missed_changes(self):
        scores = score([("Let me analyze what happened.", make_diff(score_to=1))])
        assert scores["n_unparseable"] == 1
        assert scores["loc_changes"] == 1
        assert scores["score_changes"] == 1
        assert scores["echo_mismatch"] == 0

    def test_composition_counts(self):
        scores = score([("open trunk → trunk = open; failure = none; no coin visible",
                         make_diff(prev_action="open trunk", location_to="Bedroom"))])
        assert scores["n_obj_state"] == 1
        assert scores["n_failure"] == 1
        assert scores["n_other"] == 1
