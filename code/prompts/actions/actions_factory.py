class ActionsFactory:
    def create(self):
        file_path = f"prompts/actions/actions.md"
        with open(file_path, "r") as file:
            section = file.read()
        return section