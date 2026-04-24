import io
from params.parameters import Parameters
from reviews.reader import review_reader
from reviews.reader.review_reader import ReviewReader


class TestReviewReader:
    def test_read_review(self, monkeypatch):
        params = Parameters(
            split_name="split",
            model_name="model",
            agent_name="agent",
            eval_name="eval")
        episode_id = 123

        expected_folder = "../data/artifacts/split/model/agent/eval"
        expected_file = f"{expected_folder}/split - model - agent - eval - episode-{episode_id} - review.txt"
        expected_text = "review"

        captured = {"open": None}

        def fake_open(file_path, mode="r", encoding=None, *args, **kwargs):
            captured["open"] = (file_path, mode, encoding)
            assert file_path == expected_file
            assert mode == "r"
            assert encoding == "utf-8"
            return io.StringIO(expected_text)

        reader = ReviewReader()
        monkeypatch.setattr(review_reader, "open", fake_open, raising=False)

        actual_text = reader.read(params=params, episode_id=episode_id)

        assert captured["open"] == (expected_file, "r", "utf-8")
        assert actual_text == expected_text