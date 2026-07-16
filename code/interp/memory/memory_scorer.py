from typing import Optional
from interp.game_truth import GameTruth
from interp.memory.memory_facts import MemoryFacts
from interp.memory.memory_fact_parser import clean_name

class MemoryScorer:

    def score(self, facts: MemoryFacts, truth: GameTruth, traversed: set, inventory_texts: list) -> dict:
        scores = {"link_tp": 0, "link_fp": 0, "link_unresolved": 0,
                  "traversed_total": 0, "traversed_hits": 0,
                  "obj_tp": 0, "obj_fp": 0, "obj_moved": 0, "obj_unresolved": 0,
                  "fp_links": [], "fp_objects": []}

        # Score room-link precision against the true map
        resolved_links = set()
        for room, direction, destination in facts.room_links:
            room, destination = self.resolve(room, truth.rooms), self.resolve(destination, truth.rooms)
            if room is None or destination is None:
                scores["link_unresolved"] += 1
                continue
            resolved_links.add((room, direction, destination))
            true_destination = truth.links.get((room, direction))
            if destination == true_destination:
                scores["link_tp"] += 1
            else:
                scores["link_fp"] += 1
                scores["fp_links"].append((room, direction, destination, true_destination))

        # Score room-link recall against the traversed connections
        scores["traversed_total"] = len(traversed)
        scores["traversed_hits"] = sum(1 for link in traversed if link in resolved_links)

        # Score object-location precision against the initial placements
        inventory_text = " | ".join(inventory_texts).lower()
        for object_name, room, container in facts.object_locations:
            resolved_object = self.resolve(object_name, truth.objects | set(truth.doors))
            if resolved_object is None:
                scores["obj_unresolved"] += 1
            elif room == "inventory":
                # An in-inventory claim is true if the agent held the object at some step
                if resolved_object in inventory_text:
                    scores["obj_tp"] += 1
                else:
                    scores["obj_fp"] += 1
                    scores["fp_objects"].append((resolved_object, "inventory", "never held"))
            elif self.resolve(room, truth.rooms) is None:
                scores["obj_unresolved"] += 1
            elif resolved_object in truth.doors:
                # A door location is true if the claimed room is on either side of it
                if self.resolve(room, truth.rooms) in truth.doors[resolved_object]:
                    scores["obj_tp"] += 1
                else:
                    scores["obj_fp"] += 1
                    scores["fp_objects"].append((resolved_object, self.resolve(room, truth.rooms),
                                                 " or ".join(sorted(truth.doors[resolved_object]))))
            elif resolved_object in inventory_text:
                scores["obj_moved"] += 1  # the agent moved it, so the initial placement no longer applies
            elif truth.placements[resolved_object][0] == self.resolve(room, truth.rooms):
                scores["obj_tp"] += 1
            else:
                scores["obj_fp"] += 1
                scores["fp_objects"].append((resolved_object, self.resolve(room, truth.rooms),
                                             truth.placements[resolved_object][0]))
        return scores

    def resolve(self, name: str, candidates: set) -> Optional[str]:
        # Exact match after cleaning, then unique containment in either direction
        name = clean_name(name.lower()).removeprefix("the ").strip()
        if name in candidates:
            return name
        matches = [candidate for candidate in candidates if name in candidate or candidate in name]
        return matches[0] if len(matches) == 1 else None
