import json
from typing import Optional, Tuple
from interp.game_truth import GameTruth

DIRECTIONS = {"north_of": "north", "south_of": "south", "east_of": "east", "west_of": "west"}

class GameTruthReader:

    def read(self, split_name: str, eval_name: str, episode_id: int) -> GameTruth:
        # Resolve the episode's jsonl row to its compiled game file (episode-N = row N-1)
        base_name = eval_name.split("-")[0] + "-" + eval_name.split("-")[1]
        jsonl_path = f"../data/evals/{split_name}/{base_name}/{eval_name}.jsonl"
        with open(jsonl_path, "r", encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        game_path = rows[episode_id - 1]["file_path"].replace(".ulx", ".json")

        # Read and parse the game definition
        with open(game_path, "r", encoding="utf-8") as f:
            game = json.load(f)
        return self.parse(game)

    def parse(self, game: dict) -> GameTruth:
        # Map entity ids to lowercase names (unnamed entities like P and I resolve to None)
        names = {entity_id: (info["name"] or "").lower() or None for entity_id, info in game["infos"]}

        truth = GameTruth()
        holders = {}  # object -> holder entity id, resolved to rooms after the scan

        # Scan the world facts
        for fact in game["world"]:
            arguments = [argument["name"] for argument in fact["arguments"]]
            if fact["name"] in DIRECTIONS:
                room_a, room_b = names[arguments[0]], names[arguments[1]]
                truth.rooms.update([room_a, room_b])
                truth.links[(room_b, DIRECTIONS[fact["name"]])] = room_a  # "A north_of B" = B leads north to A
            elif fact["name"] == "at":
                entity, room = arguments
                if names[entity] is None:  # the player
                    continue
                truth.objects.add(names[entity])
                truth.rooms.add(names[room])
                truth.placements[names[entity]] = (names[room], None)
            elif fact["name"] == "link":
                room_a, door, room_b = (names[argument] for argument in arguments)
                truth.rooms.update([room_a, room_b])
                truth.doors.setdefault(door, set()).update([room_a, room_b])
            elif fact["name"] in ("in", "on"):
                entity, holder = arguments
                if names[entity] is None or names[holder] is None:  # inventory-held items
                    continue
                truth.objects.add(names[entity])
                holders[names[entity]] = names[holder]

        # Resolve held objects to their holder's room
        for entity, holder in holders.items():
            room = self.resolve_room(holder, holders, truth.placements)
            truth.placements[entity] = (room, holder)
        return truth

    def resolve_room(self, holder: str, holders: dict, placements: dict) -> Optional[str]:
        while holder is not None:
            if holder in placements:
                return placements[holder][0]
            holder = holders.get(holder)
        return None
