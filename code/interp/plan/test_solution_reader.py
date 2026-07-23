import io
import json
from interp.plan import solution_reader
from interp.plan.solution_reader import SolutionReader

ROWS = [{"id": 1, "solution": "open antique trunk, take old key, go east"},
        {"id": 2, "solution": "go west, take coin"}]

class TestSolutionReader:

    def test_reads_the_episode_row_and_splits_commands(self, monkeypatch):
        opened = {}
        def fake_open(path, mode="r", encoding=None):
            opened["path"] = path
            return io.StringIO("\n".join(json.dumps(row) for row in ROWS))
        monkeypatch.setattr(solution_reader, "open", fake_open, raising=False)

        commands = SolutionReader().read("test", "tw-simple-1", episode_id=2)
        assert opened["path"] == "../data/evals/test/tw-simple/tw-simple-1.jsonl"
        assert commands == ["go west", "take coin"]
