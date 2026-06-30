import os
from params.parameters import Parameters


class MessagesWriter:

    def write(self, params: Parameters, step_id: int, subagent: str, messages: list):

        episode_id = params.episode_id

        # Create the folder
        folder_path = f"../data/artifacts/{params.split_name}/{params.model_name}/{params.agent_name}/{params.eval_name}/episode-{episode_id}/messages"
        os.makedirs(folder_path, exist_ok=True)

        # Write the system message
        if step_id == 1:
            system_message = messages[0]
            system_content = system_message["content"].replace("\n\n\n", "\n\n")
            file_name = f"{params.split_name} - {params.model_name} - {params.agent_name} - {params.eval_name} - episode-{episode_id} - step-0 - {subagent} - system-prompt.md"
            system_file_path = f"{folder_path}/{file_name}"
            with open(system_file_path, "w") as f:
                f.write(f"--- system ---\n")
                f.write(f"{system_content}\n\n")

        # Write the user and model messages
        file_name = f"{params.split_name} - {params.model_name} - {params.agent_name} - {params.eval_name} - episode-{episode_id} - step-{step_id} - {subagent}.md"
        file_path = f"{folder_path}/{file_name}"
        with open(file_path, "w") as f:
            for message in messages[1:]:
                role = message["role"]
                content = message["content"]
                content = content.replace("\n\n\n", "\n\n")
                f.write(f"--- {role} ---\n")
                f.write(f"{content}\n\n")




