from unittest.mock import MagicMock, call, mock_open, patch
from common.log import Log, BOLD_WHITE, WHITE, YELLOW, ORANGE, RED, RESET
from common.parameters import Parameters
from renderers.renderer_factory import RendererFactory
from states.global_state import GlobalState
from states.task_state import TaskState
from states.step_state import StepState
from states.env_state import EnvState
from states.agent_state import AgentState


class TestLog:
    @patch("builtins.print")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_log_calls(self, mock_makedirs, mock_open_fn, mock_print):
        renderer = RendererFactory.create()
        params = Parameters(
            agent_name="test_agent",
            model_name="test_model",
            env_name="test_env",
            eval_name="test_eval",
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
        expected_dir = "../data/logs/test_agent - test_model - test_eval"
        mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)

        # Assert file was opened
        expected_file = f"{expected_dir}/1.txt"
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
