from common.parameters import Parameters

class ExamplesFactory:
    def create(self, params: Parameters):

        # Load section from file
        file_path = f"prompts/examples/examples.md"
        with open(file_path, "r") as file:
            examples = file.read()

        # Filter thoughts
        if not params.use_reasoner and not params.use_react:
            examples = self.remove_line(examples, "Thought")

        # Filter action
        # Note: Actor is always used, so no filtering needed

        # Filter summaries
        if not params.use_summarizer:
            examples = self.remove_line(examples, "Summary")

        return examples

    @staticmethod
    def remove_line(section: str, subagent_name: str) -> str:
        filtered_lines = []
        for line in section.splitlines():
            subagent_tag = f"  {subagent_name}: "
            if subagent_tag not in line:
                filtered_lines.append(line)
        return "\n".join(filtered_lines)