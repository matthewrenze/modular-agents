from memory.memory_manager import MemoryManager

class TestMemoryManager:
    def test_execute(self):

        memories = {
            1: "memory 1",
            2: "memory 2",
        }

        updates = """
                create: memory 3
                delete: 2
                """.strip()
        manager = MemoryManager()
        actual = manager.execute(memories, updates)

        assert actual == {
            1: "memory 1",
            3: "memory 3",
        }