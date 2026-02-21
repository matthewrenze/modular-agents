from memory.memory_manager import MemoryManager

class TestMemoryManager:
    def test_execute(self):

        memories = {
            1: "memory 1",
            2: "memory 2A",
            3: "memory 3",
        }

        updates = """
                create: memory 4
                update: 2 = memory 2B
                delete: 3
                """.strip()
        manager = MemoryManager()
        actual = manager.execute(memories, updates)

        assert actual == {
            1: "memory 1",
            2: "memory 2B",
            4: "memory 4",
        }