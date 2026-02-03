
class MemoryManager:

    def execute(self, memories, updates: str):

        # Get the next id
        next_id = 1 \
            if not memories \
            else max(memories.keys()) + 1

        # Process each operation line by line
        for line in updates.splitlines():
            line = line.strip()
            if not line:
                continue

            # Parse the operation
            operation, _, value = line.partition(":")
            operation = operation.strip().lower()
            value = value.strip()

            # Execute create
            if operation == "create":
                memory = value
                memories[next_id] = memory
                next_id += 1

            # Execute delete
            elif operation == "delete":
                id = int(value)
                if not id in memories:
                    raise ValueError(f"Memory ID {id} does not exist for deletion.")
                del memories[id]

            # Handle unknown operation
            else:
                raise ValueError(f"Unknown memory operation: {line}")

        return memories