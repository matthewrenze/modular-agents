from dataclasses import dataclass, field
from typing import Dict
import pandas as pd
from params.parameters import Parameters
from states.global_state import GlobalState

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
