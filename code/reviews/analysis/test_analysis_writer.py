import io
from params.parameters import Parameters
from reviews.analysis import analysis_writer
from reviews.analysis.analysis_writer import AnalysisWriter



class TestAnalysisWriter:
    def test_write_review(self, monkeypatch):
        params = Parameters(
            split_name="test",
            agent_name="agent",
            model_name="model",
            eval_name="eval")
        analysis = "analysis"

        expected_folder = "../data/artifacts/test/model/agent"
        expected_file = f"{expected_folder}/test - model - agent - analysis.txt"
        expected_text = "analysis"

        captured = {"makedirs": None, "open": None, "text": None}

        def fake_makedirs(path, exist_ok=False):
            captured["makedirs"] = (path, exist_ok)

        def fake_open(file_path, mode="r", encoding=None, *args, **kwargs):
            captured["open"] = (file_path, mode, encoding)
            assert file_path == expected_file
            assert mode == "w"
            assert encoding == "utf-8"
            return _CaptureWriter(lambda text: captured.__setitem__("text", text))

        writer = AnalysisWriter()
        monkeypatch.setattr(analysis_writer.os, "makedirs", fake_makedirs, raising=True)
        monkeypatch.setattr(analysis_writer, "open", fake_open, raising=False)

        writer.write(
            params=params,
            analysis=analysis)

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


