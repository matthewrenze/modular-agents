import io
from unittest.mock import call, patch
from logs.log import Log, BOLD_WHITE, WHITE, YELLOW, ORANGE, RED, RESET
from renderers.renderer_factory import RendererFactory


class TestLog:
    @patch("builtins.print")
    def test_log_calls(self, mock_print):
        renderer = RendererFactory.create()
        file = io.StringIO()

        # Act
        log = Log(file, renderer)
        log.head("head")
        log.info("info")
        log.debug("debug")
        log.warning("warning")
        log.error("error")

        # Assert file contents
        assert file.getvalue() == (
            "head\n"
            "info\n"
            "Debug: debug\n"
            "Warning: warning\n"
            "Error: error\n")

        # Assert the file is closed
        log.close()
        assert file.closed

        # Assert console output
        mock_print.assert_has_calls(
            [
                call(f"{BOLD_WHITE}head{RESET}"),
                call(f"{WHITE}info{RESET}"),
                call(f"{YELLOW}Debug: debug{RESET}"),
                call(f"{ORANGE}Warning: warning{RESET}"),
                call(f"{RED}Error: error{RESET}"),
            ]
        )
