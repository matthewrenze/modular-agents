from interp.game_truth import GameTruth
from interp.memory.memory_facts import MemoryFacts
from interp.memory.memory_scorer import MemoryScorer

def make_truth():
    return GameTruth(
        rooms={"dish-pit", "steam room", "closet"},
        links={("dish-pit", "north"): "steam room",
               ("steam room", "south"): "dish-pit",
               ("steam room", "east"): "closet",
               ("closet", "west"): "steam room"},
        objects={"coin", "gold key", "chest", "yellow potato"},
        placements={"coin": ("steam room", None),
                    "chest": ("dish-pit", None),
                    "gold key": ("dish-pit", "chest"),
                    "yellow potato": ("closet", None)},
        doors={"wooden door": {"steam room", "closet"}})

class TestMemoryScorer:

    def test_link_precision(self):
        facts = MemoryFacts(room_links=[
            ("dish-pit", "north", "steam room"),   # true
            ("steam room", "south", "closet"),     # false (south = dish-pit)
            ("attic", "north", "closet"),          # unresolvable room name
        ])
        scores = MemoryScorer().score(facts, make_truth(), traversed=set(), inventory_texts=[])
        assert scores["link_tp"] == 1
        assert scores["link_fp"] == 1
        assert scores["link_unresolved"] == 1
        assert scores["fp_links"] == [("steam room", "south", "closet", "dish-pit")]

    def test_link_recall(self):
        facts = MemoryFacts(room_links=[("dish-pit", "north", "steam room")])
        traversed = {("dish-pit", "north", "steam room"), ("steam room", "east", "closet")}
        scores = MemoryScorer().score(facts, make_truth(), traversed=traversed, inventory_texts=[])
        assert scores["traversed_total"] == 2
        assert scores["traversed_hits"] == 1

    def test_fuzzy_room_names_resolve_by_unique_containment(self):
        facts = MemoryFacts(room_links=[("pit", "north", "steam room")])
        scores = MemoryScorer().score(facts, make_truth(), traversed=set(), inventory_texts=[])
        assert scores["link_tp"] == 1
        assert scores["link_unresolved"] == 0

    def test_object_precision(self):
        facts = MemoryFacts(object_locations=[
            ("coin", "steam room", None),   # true
            ("gold key", "closet", None),   # false (dish-pit)
            ("lamp", "closet", None),       # unresolvable object name
        ])
        scores = MemoryScorer().score(facts, make_truth(), traversed=set(),
                                      inventory_texts=["You are carrying nothing."])
        assert scores["obj_tp"] == 1
        assert scores["obj_fp"] == 1
        assert scores["obj_unresolved"] == 1
        assert scores["fp_objects"] == [("gold key", "closet", "dish-pit")]

    def test_object_names_resolve_by_reverse_containment(self):
        facts = MemoryFacts(object_locations=[("raw yellow potato", "closet", None)])
        scores = MemoryScorer().score(facts, make_truth(), traversed=set(), inventory_texts=[])
        assert scores["obj_tp"] == 1
        assert scores["obj_unresolved"] == 0

    def test_door_locations_score_against_adjacent_rooms(self):
        facts = MemoryFacts(object_locations=[("wooden door", "closet", None),
                                              ("wooden door", "dish-pit", None)])
        scores = MemoryScorer().score(facts, make_truth(), traversed=set(), inventory_texts=[])
        assert scores["obj_tp"] == 1
        assert scores["obj_fp"] == 1

    def test_inventory_claims_score_against_inventory_texts(self):
        facts = MemoryFacts(object_locations=[("coin", "inventory", None),
                                              ("gold key", "inventory", None)])
        scores = MemoryScorer().score(facts, make_truth(), traversed=set(),
                                      inventory_texts=["You are carrying: a coin."])
        assert scores["obj_tp"] == 1
        assert scores["obj_fp"] == 1

    def test_moved_objects_are_excluded(self):
        facts = MemoryFacts(object_locations=[("coin", "steam room", None)])
        scores = MemoryScorer().score(facts, make_truth(), traversed=set(),
                                      inventory_texts=["You are carrying nothing.", "You are carrying: a coin."])
        assert scores["obj_moved"] == 1
        assert scores["obj_tp"] == 0
