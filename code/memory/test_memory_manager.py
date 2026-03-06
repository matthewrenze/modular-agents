from memory.memory_manager import MemoryManager

class TestMemoryManager:
    def test_execute(self):

        memories = {
            "item 1": "value 1",
            "item 2": "key 2 = value 2",
            "item 3": "key 3 = {value 3A, value 3B}",
        }

        updates = """
                item 1: value 1B
                item 3:
                item 4: value 4
                """.strip()
        manager = MemoryManager()
        actual = manager.execute(memories, updates)

        assert actual == {
            "item 1": "value 1B",
            "item 2": "key 2 = value 2",
            "item 4": "value 4",
        }