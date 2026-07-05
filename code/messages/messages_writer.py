import os
from artifacts.artifacts import Artifacts
from params.parameters import Parameters


class MessagesWriter:

    def __init__(self, artifacts: Artifacts):
        self.artifacts = artifacts

    def write(self, params: Parameters, step_id: int, subagent: str, messages: list):

        # Create the folder
        folder_path = f"{self.artifacts.get_episode_folder_path(params)}/messages"
        os.makedirs(folder_path, exist_ok=True)

        # Write the system message
        if step_id == 1:
            system_message = messages[0]
            system_content = system_message["content"].replace("\n\n\n", "\n\n")
            file_name = self.artifacts.get_file_name(params, f"step-0 - {subagent} - system-prompt.md")
            system_file_path = f"{folder_path}/{file_name}"
            with open(system_file_path, "w") as f:
                f.write(f"--- system ---\n")
                f.write(f"{system_content}\n\n")

        # Write the user and model messages
        file_name = self.artifacts.get_file_name(params, f"step-{step_id} - {subagent}.md")
        file_path = f"{folder_path}/{file_name}"
        with open(file_path, "w") as f:
            for message in messages[1:]:
                role = message["role"]
                content = message["content"]
                content = content.replace("\n\n\n", "\n\n")
                f.write(f"--- {role} ---\n")
                f.write(f"{content}\n\n")




