import os
from params.parameters import Parameters

class ReviewWriter:
    def write(self, params: Parameters, episode_id: int, review: str):

        # Create the folder
        folder_path = f"../data/reviews/{params.model_name} - {params.agent_name} - {params.eval_name}"
        os.makedirs(folder_path, exist_ok=True)

        # Write the review
        file_path = f"{folder_path}/{episode_id}.txt"
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(review)