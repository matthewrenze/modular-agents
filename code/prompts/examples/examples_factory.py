import re
from params.parameters import Parameters

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

        # Filter plans
        if not params.use_planner:
            examples = self.remove_line(examples, r"^Plan:")
            examples = self.remove_line(examples, r"^  (\d+) \[(.?)\]")
            examples = self.remove_block(examples, r"^  Plan:")

        # Filter memories
        if not params.use_memorizer:
            examples = self.remove_line(examples, r"^Memories:")
            examples = self.remove_line(examples, r"^  \d+:")
            examples = self.remove_block(examples, r"^  Memory:")

        # Filter thoughts
        if not params.use_reasoner and not params.use_react_kn:
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

    @staticmethod
    def remove_block(section: str, regex: str) -> str:
        filtered_lines = []
        pattern = re.compile(regex)
        skip_block = False
        for line in section.splitlines():
            if pattern.search(line):
                skip_block = True
            elif skip_block and not line.startswith("    "):
                skip_block = False

            if not skip_block:
                filtered_lines.append(line)

        return "\n".join(filtered_lines)