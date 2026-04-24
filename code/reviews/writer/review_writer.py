import os
from params.parameters import Parameters

class ReviewWriter:
    def write(self, params: Parameters, episode_id: int, review: str):

        # Create the file path
        folder_path = f"../data/artifacts/{params.split_name}/{params.model_name}/{params.agent_name}/{params.eval_name}/episode-{episode_id}"
        file_name = f"{params.split_name} - {params.model_name} - {params.agent_name} - {params.eval_name} - episode-{episode_id} - review.txt"
        file_path = f"{folder_path}/{file_name}"

        # Write the review
        os.makedirs(folder_path, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(review)