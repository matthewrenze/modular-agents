class MemoriesRenderer:
    def render(self, memories: dict[str, str]) -> str:

        if not memories:
            return "Memories: N/A\n"

        output = "Memories:\n"
        for id, memory in memories.items():
            output += f"  {id}: {memory}\n"

        return output