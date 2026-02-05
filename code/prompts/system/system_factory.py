from common.parameters import Parameters

class SystemFactory:
    def create(self, params: Parameters, subagent_name: str):

        # Load section from file
        file_path = f"prompts/system/system.md"
        with open(file_path, "r") as file:
            section = file.read()

        # Filter tasker
        if not params.use_tasker:
            section = self.remove_line(section, "Tasker")

        # Filter summarizer
        if not params.use_summarizer:
            section = self.remove_line(section, "Summarizer")

        # Filter planner
        if not params.use_planner:
            section = self.remove_line(section, "Planner")

        # Filter memorizer
        if not params.use_memorizer:
            section = self.remove_line(section, "Memorizer")

        # Filter reasoner
        if not params.use_reasoner:
            section = self.remove_line(section, "Reasoner")

        # Add "(you)" tag to the specified subagent
        subagent_name = subagent_name.capitalize()
        section = self.add_you_tag(section, subagent_name)

        return section

    @staticmethod
    def remove_line(section: str, subagent_name: str) -> str:
        filtered_lines = []
        for line in section.splitlines():
            subagent_tag = f" - {subagent_name} - "
            if subagent_tag not in line:
                filtered_lines.append(line)
        return "\n".join(filtered_lines)

    @staticmethod
    def add_you_tag(section: str, subagent_name: str):
        subagent_tag = f" - {subagent_name} - "
        new_subagent_tag = f" - {subagent_name} (you) - "
        section = section.replace(subagent_tag, new_subagent_tag)
        return section