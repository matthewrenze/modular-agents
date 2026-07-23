import pandas as pd
from params.parameters import Parameters
from states.global_state import GlobalState
from interp.episode_extract import EpisodeExtract

class TestEpisodeExtract:
    def test_env_diffs(self):

        # Create the per-step details
        details = pd.DataFrame([
            {"step_id": 1, "feedback": "", "location": "Dish-Pit", "inventory": "nothing", "score": 0, "summary": "start", "thought": "t1", "action": "go north"},
            {"step_id": 2, "feedback": "You arrive in a steam room.", "location": "Steam Room", "inventory": "nothing", "score": 0, "summary": "s2", "thought": "t2", "action": "take coin"},
            {"step_id": 3, "feedback": "Taken.", "location": "Steam Room", "inventory": "a coin", "score": 1, "summary": "s3", "thought": "t3", "action": "go south"},
        ])

        # Create the episode extract
        extract = EpisodeExtract(params=Parameters(), state=GlobalState(), details=details, last_messages={})

        # Compute the env diffs
        diffs = extract.env_diffs()
        assert len(diffs) == 3

        # Verify the first step (no previous state)
        d1 = diffs[0]
        assert d1["step_id"] == 1
        assert d1["prev_action"] == ""
        assert d1["location_from"] == ""
        assert d1["location_to"] == "Dish-Pit"
        assert d1["inventory_from"] == ""
        assert d1["inventory_to"] == "nothing"
        assert d1["score_from"] == 0
        assert d1["score_to"] == 0
        assert d1["feedback"] == ""

        # Verify a location change
        d2 = diffs[1]
        assert d2["step_id"] == 2
        assert d2["prev_action"] == "go north"
        assert d2["location_from"] == "Dish-Pit"
        assert d2["location_to"] == "Steam Room"
        assert d2["feedback"] == "You arrive in a steam room."

        # Verify an inventory and score change
        d3 = diffs[2]
        assert d3["step_id"] == 3
        assert d3["prev_action"] == "take coin"
        assert d3["location_from"] == "Steam Room"
        assert d3["location_to"] == "Steam Room"
        assert d3["inventory_from"] == "nothing"
        assert d3["inventory_to"] == "a coin"
        assert d3["score_from"] == 0
        assert d3["score_to"] == 1

    def test_traversed_links(self):

        # Create the per-step details (successful moves, a failed move, and a non-move)
        details = pd.DataFrame([
            {"step_id": 1, "feedback": "", "location": "Dish-Pit", "inventory": "nothing", "score": 0, "summary": "", "thought": "", "action": "go north"},
            {"step_id": 2, "feedback": "", "location": "Steam Room", "inventory": "nothing", "score": 0, "summary": "", "thought": "", "action": "go west"},
            {"step_id": 3, "feedback": "You can't go that way.", "location": "Steam Room", "inventory": "nothing", "score": 0, "summary": "", "thought": "", "action": "east"},
            {"step_id": 4, "feedback": "", "location": "Closet", "inventory": "nothing", "score": 0, "summary": "", "thought": "", "action": "take coin"},
            {"step_id": 5, "feedback": "Taken.", "location": "Closet", "inventory": "a coin", "score": 1, "summary": "", "thought": "", "action": "go north"},
        ])
        extract = EpisodeExtract(params=Parameters(), state=GlobalState(), details=details, last_messages={})

        # Successful moves are recorded lowercase; failed moves, non-moves, and the last action are not
        assert extract.traversed_links() == {("dish-pit", "north", "steam room"),
                                             ("steam room", "east", "closet")}

