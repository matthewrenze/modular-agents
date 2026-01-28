import io
from common.parameters import Parameters
from reviews.review import Review
from reviews import review_writer
from reviews.review_writer import ReviewWriter

review = Review(
    steps={
        "Step 1": "N/A",
        "Step 2": "N/A",
        "Step 3": "An error"
    },
    loops="A loop",
    summary="A summary",
    category="A category",
    advice="Some advice"
)

expected_text = """
Steps:
  Step 1: N/A
  Step 2: N/A
  Step 3: An error
Loops: A loop
Summary: A summary
Category: A category
Advice: Some advice
""".lstrip()

class TestReviewWriter:
    def test_write_review(self, monkeypatch):
        params = Parameters(
            agent_name="agent-a",
            model_name="model-b",
            eval_name="eval-c")
        episode_id = 123
        expected_folder = "../data/reviews/agent-a - model-b - eval-c"
        expected_file = f"{expected_folder}/{episode_id}.txt"
        captured = {"makedirs": None, "open": None, "text": None}

        def fake_makedirs(path, exist_ok=False):
            captured["makedirs"] = (path, exist_ok)

        def fake_open(file_path, mode="r", encoding=None, *args, **kwargs):
            captured["open"] = (file_path, mode, encoding)
            assert file_path == expected_file
            assert mode == "w"
            assert encoding == "utf-8"
            return _CaptureWriter(lambda text: captured.__setitem__("text", text))

        writer = ReviewWriter()
        monkeypatch.setattr(review_writer.os, "makedirs", fake_makedirs, raising=True)
        monkeypatch.setattr(review_writer, "open", fake_open, raising=False)

        writer.write(
            review=review,
            params=params,
            episode_id=episode_id)

        assert captured["makedirs"] == (expected_folder, True)
        assert captured["open"] == (expected_file, "w", "utf-8")
        assert captured["text"] == expected_text


class _CaptureWriter(io.StringIO):
    def __init__(self, on_close):
        super().__init__()
        self._on_close = on_close

    def close(self):
        self._on_close(self.getvalue())
        super().close()


