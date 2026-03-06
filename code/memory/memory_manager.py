class MemoryManager:
    def execute(self, memories: dict[str, str], updates: str) -> dict[str, str]:

        # If there are no memories, create an empty dict
        if memories is None:
            memories = {}

        for update_line in updates.splitlines():
            update_line = update_line.strip()

            # Skip empty lines
            if not update_line:
                continue

            # Handle invalid update lines
            if ":" not in update_line:
                raise ValueError(f"Invalid memory update: {update_line}")

            # Parse the memory key and value
            key, value = update_line.split(":", 1)
            key = key.strip()
            value = value.strip()

            if value == "":
                # Delete the memory
                memories.pop(key, None)
            else:
                # Add or update the memory
                memories[key] = value

        return memories