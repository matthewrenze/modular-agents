import re
from dataclasses import dataclass, field
from typing import Dict
import pandas as pd
from params.parameters import Parameters
from states.global_state import GlobalState

MOVE_PATTERN = re.compile(r"^(?:go|move|head|walk|run|travel)?\s*(north|south|east|west)$")

@dataclass
class EpisodeExtract:
    params: Parameters
    state: GlobalState
    details: pd.DataFrame
    last_messages: Dict[int, Dict[str, str]] = field(default_factory=dict)

    def env_diffs(self) -> list:
        # Pair each step's env state with the previous step's state and action
        diffs = []
        prev = None
        for row in self.details.to_dict("records"):
            diffs.append({
                "step_id": row["step_id"],
                "prev_action": prev["action"] if prev else "",
                "location_from": prev["location"] if prev else "",
                "location_to": row["location"],
                "inventory_from": prev["inventory"] if prev else "",
                "inventory_to": row["inventory"],
                "score_from": prev["score"] if prev else 0,
                "score_to": row["score"],
                "feedback": row["feedback"],
            })
            prev = row
        return diffs

    def traversed_links(self) -> set:
        # Collect the directed room connections confirmed by successful moves
        links = set()
        for diff in self.env_diffs():
            move = MOVE_PATTERN.match(str(diff["prev_action"]).strip().lower())
            if move and diff["location_from"] and diff["location_to"] != diff["location_from"]:
                links.add((diff["location_from"].strip().lower(), move.group(1),
                           diff["location_to"].strip().lower()))
        return links
