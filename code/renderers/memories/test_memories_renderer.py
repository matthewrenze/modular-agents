from renderers.memories.memories_renderer import MemoriesRenderer

class TestMemoriesRenderer:
    def test_render(self):

        memories = {
            1: "memory 1",
            2: "memory 2"
        }

        renderer = MemoriesRenderer()
        rendered_output = renderer.render(memories)

        expected_output = (
            "Memories:\n"
            "  1: memory 1\n"
            "  2: memory 2\n")

        assert rendered_output == expected_output

    def test_render_empty(self):

        memories = {}

        renderer = MemoriesRenderer()
        rendered_output = renderer.render(memories)

        expected_output = "Memories: N/A\n"

        assert rendered_output == expected_output
