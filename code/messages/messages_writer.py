import os
from common.parameters import Parameters


class MessagesWriter:

    def write(self, params: Parameters, episode_id: int, step_id: int, subagent: str, messages: list):

        # Create the folder
        folder_path = f"../data/messages/{params.agent_name} - {params.model_name} - {params.eval_name}"
        os.makedirs(folder_path, exist_ok=True)

        # Write the messages
        file_path = f"{folder_path}/{episode_id}-{step_id}-{subagent}.md"
        with open(file_path, "w") as f:
            for message in messages:
                role = message["role"]
                content = message["content"]
                content = content.replace("\n\n\n", "\n\n")
                f.write(f"--- {role} ---\n")
                f.write(f"{content}\n\n")




