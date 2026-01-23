from common.parameters import Parameters

class ProcessFactory:

    def create(self, params: Parameters, subagent_name: str):

        # Load section from file
        file_path = f"prompts/process/process.md"
        with open(file_path, "r") as file:
            section = file.read()

        # Filter tasker
        if not params.use_tasker:
            section = self.remove_line(section, "Tasker")

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
            subagent_tag = f"({subagent_name})"
            if subagent_tag not in line:
                filtered_lines.append(line)
        return "\n".join(filtered_lines)

    @staticmethod
    def add_you_tag(section: str, subagent_name: str):
        subagent_tag = f"({subagent_name})"
        new_subagent_tag = f"(you)"
        section = section.replace(subagent_tag, new_subagent_tag)
        return section