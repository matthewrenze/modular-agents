import re
from common.parameters import Parameters

class ExamplesFactory:
    def create(self, params: Parameters):

        # Load section from file
        file_path = f"prompts/examples/examples.md"
        with open(file_path, "r") as file:
            examples = file.read()

        # Filter summaries
        if not params.use_summarizer:
            examples = self.remove_line(examples, r"^History:")
            examples = self.remove_line(examples, r"^  Step \d+:")
            examples = self.remove_line(examples, r"^  Summary:")

        # Filter memories
        if not params.use_memorizer:
            examples = self.remove_line(examples, r"^Memories:")
            examples = self.remove_line(examples, r"^  \d+:")
            examples = self.remove_line(examples, r"^  Memory:")
            examples = self.remove_line(examples, r"^    add:")
            examples = self.remove_line(examples, r"^    remove:")

        # Filter thoughts
        if not params.use_reasoner and not params.use_react:
            examples = self.remove_line(examples, r"^  Thought:")

        # Filter action
        # Note: Actor is always used, so no filtering needed

        return examples

    @staticmethod
    def remove_line(section: str, regex: str) -> str:
        filtered_lines = []
        pattern = re.compile(regex)
        for line in section.splitlines():
            if not pattern.search(line):
                filtered_lines.append(line)
        return "\n".join(filtered_lines)