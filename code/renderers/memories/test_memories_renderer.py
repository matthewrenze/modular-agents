from renderers.memories.memories_renderer import MemoriesRenderer

class TestMemoriesRenderer:
    def test_render(self):
        memories = {
            1: "memory 1",
            2: "memory 2"}
        expected = (
            "Memories:\n"
            "  1: memory 1\n"
            "  2: memory 2\n")

        renderer = MemoriesRenderer()
        actual = renderer.render(memories)

        assert actual == expected

    def test_render_empty(self):
        memories = {}
        expected = "Memories: N/A\n"

        renderer = MemoriesRenderer()
        actual = renderer.render(memories)

        assert actual == expected
