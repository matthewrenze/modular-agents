from unittest.mock import call, mock_open, patch
from logs.log import Log, BOLD_WHITE, WHITE, YELLOW, ORANGE, RED, RESET
from params.parameters import Parameters
from renderers.renderer_factory import RendererFactory


class TestLog:
    @patch("builtins.print")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_log_calls(self, mock_makedirs, mock_open_fn, mock_print):
        renderer = RendererFactory.create()
        params = Parameters(
            split_name="test-split",
            model_name="test-model",
            agent_name="test-agent",
            env_name="test-env",
            eval_name="test-eval",
            max_steps=10)
        episode_id = 1

        # Act
        log = Log(renderer, params, episode_id)
        log.head("head")
        log.info("info")
        log.debug("debug")
        log.warning("warning")
        log.error("error")
        log.close()

        # Assert folder was created
        expected_dir = "../data/artifacts/test-split/test-model/test-agent/test-eval/episode-1"
        mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)

        # Assert file was opened
        expected_file = f"{expected_dir}/test-split - test-model - test-agent - test-eval - episode-1 - log.txt"
        mock_open_fn.assert_called_once_with(
            expected_file, "w", encoding="utf-8", newline="\n")

        # Assert file contents
        file_handle = mock_open_fn()
        file_handle.write.assert_has_calls(
            [
                call("head\n"),
                call("info\n"),
                call("Debug: debug\n"),
                call("Warning: warning\n"),
                call("Error: error\n"),
            ]
        )
        file_handle.flush.assert_called_once()
        file_handle.close.assert_called_once()

        # Assert console output ---
        mock_print.assert_has_calls(
            [
                call(f"{BOLD_WHITE}head{RESET}"),
                call(f"{WHITE}info{RESET}"),
                call(f"{YELLOW}Debug: debug{RESET}"),
                call(f"{ORANGE}Warning: warning{RESET}"),
                call(f"{RED}Error: error{RESET}"),
            ]
        )
