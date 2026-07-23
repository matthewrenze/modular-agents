import io
import json
from interp import game_truth_reader
from interp.game_truth_reader import GameTruthReader

def fact(name, *entity_ids):
    return {"name": name, "arguments": [{"name": entity_id} for entity_id in entity_ids]}

GAME = {
    "world": [
        fact("at", "P", "r_0"),
        fact("north_of", "r_1", "r_0"),   # r_1 is north of r_0
        fact("south_of", "r_0", "r_1"),
        fact("east_of", "r_2", "r_1"),
        fact("west_of", "r_1", "r_2"),
        fact("at", "o_0", "r_1"),         # coin in steam room
        fact("at", "c_0", "r_0"),         # chest in dish-pit
        fact("in", "k_0", "c_0"),         # gold key in chest
        fact("at", "s_0", "r_2"),         # table in closet
        fact("on", "f_0", "s_0"),         # apple on table
        fact("free", "r_0", "r_1"),
        fact("link", "r_1", "d_0", "r_2"),  # wooden door between steam room and closet
        fact("link", "r_2", "d_0", "r_1"),
    ],
    "infos": [
        ["P", {"name": None}],
        ["I", {"name": None}],
        ["r_0", {"name": "dish-pit"}],
        ["r_1", {"name": "Steam Room"}],
        ["r_2", {"name": "closet"}],
        ["o_0", {"name": "coin"}],
        ["c_0", {"name": "chest"}],
        ["k_0", {"name": "gold key"}],
        ["s_0", {"name": "table"}],
        ["f_0", {"name": "apple"}],
        ["d_0", {"name": "wooden door"}],
    ],
}

class TestGameTruthReader:

    def test_parse_rooms_and_links(self):
        truth = GameTruthReader().parse(GAME)
        assert truth.rooms == {"dish-pit", "steam room", "closet"}
        assert truth.links == {("dish-pit", "north"): "steam room",
                               ("steam room", "south"): "dish-pit",
                               ("steam room", "east"): "closet",
                               ("closet", "west"): "steam room"}

    def test_parse_placements_resolve_containment(self):
        truth = GameTruthReader().parse(GAME)
        assert truth.objects == {"coin", "chest", "gold key", "table", "apple"}
        assert truth.placements == {"coin": ("steam room", None),
                                    "chest": ("dish-pit", None),
                                    "gold key": ("dish-pit", "chest"),
                                    "table": ("closet", None),
                                    "apple": ("closet", "table")}

    def test_parse_doors(self):
        truth = GameTruthReader().parse(GAME)
        assert truth.doors == {"wooden door": {"steam room", "closet"}}

    def test_read_resolves_episode_to_game_file(self, monkeypatch):
        rows = [{"file_path": "../data/evals/test/tw-coin/files/tw-coin-1-1.ulx"},
                {"file_path": "../data/evals/test/tw-coin/files/tw-coin-1-2.ulx"}]
        jsonl = "\n".join(json.dumps(row) for row in rows) + "\n"
        opened = []

        def fake_open(file_path, mode="r", encoding=None, *args, **kwargs):
            opened.append(file_path)
            if file_path.endswith(".jsonl"):
                return io.StringIO(jsonl)
            return io.StringIO(json.dumps(GAME))
        monkeypatch.setattr(game_truth_reader, "open", fake_open, raising=False)

        truth = GameTruthReader().read("test", "tw-coin-1", 2)
        assert opened == ["../data/evals/test/tw-coin/tw-coin-1.jsonl",
                          "../data/evals/test/tw-coin/files/tw-coin-1-2.json"]
        assert truth.rooms == {"dish-pit", "steam room", "closet"}
