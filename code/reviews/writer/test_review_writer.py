import io
from artifacts.artifacts import Artifacts
from params.parameters import Parameters
from reviews.writer import review_writer
from reviews.writer.review_writer import ReviewWriter



class TestReviewWriter:
    def test_write_review(self, monkeypatch):
        episode_id = 123
        params = Parameters(
            version="version",
            split_name="split",
            model_name="model",
            agent_name="agent",
            eval_name="eval",
            episode_id=episode_id)
        review = "review"

        expected_folder = f"../data/artifacts/version/split/model/agent/eval/episode-{episode_id}"
        expected_file = f"{expected_folder}/version - split - model - agent - eval - episode-{episode_id} - review.txt"
        expected_text = "review"

        captured = {"open": None, "text": None}

        def fake_open(file_path, mode="r", encoding=None, *args, **kwargs):
            captured["open"] = (file_path, mode, encoding)
            assert file_path == expected_file
            assert mode == "w"
            assert encoding == "utf-8"
            return _CaptureWriter(lambda text: captured.__setitem__("text", text))

        writer = ReviewWriter(Artifacts())
        monkeypatch.setattr(Artifacts, "create_episode", lambda self, params: self.get_episode_folder_path(params))
        monkeypatch.setattr(review_writer, "open", fake_open, raising=False)

        writer.write(
            review=review,
            params=params)

        assert captured["open"] == (expected_file, "w", "utf-8")
        assert captured["text"] == expected_text


class _CaptureWriter(io.StringIO):
    def __init__(self, on_close):
        super().__init__()
        self._on_close = on_close

    def close(self):
        self._on_close(self.getvalue())
        super().close()


