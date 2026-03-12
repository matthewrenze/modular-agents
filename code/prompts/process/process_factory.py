from params.parameters import Parameters

class ProcessFactory:

    def create(self, params: Parameters, subagent_name: str):

        # Load section from file
        file_path = f"prompts/process/process.md"
        with open(file_path, "r") as file:
            section = file.read()

        # Filter "We will also have access to the following:"
        if not params.use_summarizer \
                and not params.use_memorizer \
                and not params.use_planner:
            section = self.remove_line(section, "We will also have access to the following:")

        # Filter summarizer
        if not params.use_summarizer:
            section = self.remove_subagent_line(section, "History")
            section = self.remove_subagent_line(section, "Summary")

        # Filter memorizer
        if not params.use_memorizer:
            section = self.remove_subagent_line(section, "Memories")
            section = self.remove_subagent_line(section, "Memory")

        # Filter planner
        if not params.use_planner:
            section = self.remove_subagent_line(section, "Plan")

        # Filter reasoner
        if not params.use_reasoner:
            section = self.remove_subagent_line(section, "Thought")

        # Add "(you)" tag to the specified subagent
        subagent_name = subagent_name.capitalize()
        section = self.add_you_tag(section, subagent_name)

        return section

    @staticmethod
    def remove_subagent_line(section: str, subagent_name: str) -> str:
        filtered_lines = []
        for line in section.splitlines():
            subagent_tag = f" - {subagent_name}"
            if subagent_tag not in line:
                filtered_lines.append(line)
        return "\n".join(filtered_lines)

    @staticmethod
    def remove_line(section: str, tag: str) -> str:
        filtered_lines = []
        for line in section.splitlines():
            if tag not in line:
                filtered_lines.append(line)
        return "\n".join(filtered_lines)

    @staticmethod
    def add_you_tag(section: str, subagent_name: str):
        subagent_tag = f"({subagent_name})"
        new_subagent_tag = f"(you)"
        section = section.replace(subagent_tag, new_subagent_tag)
        return section