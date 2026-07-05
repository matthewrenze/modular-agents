from unittest.mock import mock_open, patch
from artifacts.artifacts import Artifacts
from logs.log_factory import LogFactory
from params.parameters import Parameters
from renderers.renderer_factory import RendererFactory


class TestLogFactory:
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_create(self, mock_makedirs, mock_open_fn):
        renderer = RendererFactory.create()
        params = Parameters(
            version="test-version",
            split_name="test-split",
            model_name="test-model",
            agent_name="test-agent",
            eval_name="test-eval",
            episode_id=1)

        # Act
        log = LogFactory().create(renderer, Artifacts(), params)

        # Assert folder was created
        expected_dir = "../data/artifacts/test-version/test-split/test-model/test-agent/test-eval/episode-1"
        mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)

        # Assert file was opened
        expected_file = f"{expected_dir}/test-version - test-split - test-model - test-agent - test-eval - episode-1 - log.txt"
        mock_open_fn.assert_called_once_with(
            expected_file, "w", encoding="utf-8", newline="\n")

        # Assert the log holds the opened file
        assert log.file is mock_open_fn()
