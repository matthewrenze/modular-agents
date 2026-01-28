import os
import yaml
from common.parameters import Parameters
from reviews.review import Review

class ReviewWriter:
    def write(self, review: Review, params: Parameters, episode_id: int):

        # Convert to dictionary
        data = dict(review)

        # Capitalize first letter of each YAML property
        data = { (k.capitalize()) if isinstance(k, str) else k: v for k, v in data.items() }

        # Create the folder
        folder_path = f"../data/reviews/{params.agent_name} - {params.model_name} - {params.eval_name}"
        os.makedirs(folder_path, exist_ok=True)

        # Write YAML to the file
        file_path = f"{folder_path}/{episode_id}.txt"
        with open(file_path, "w", encoding="utf-8") as file:
            yaml.safe_dump(data, file, allow_unicode=True, sort_keys=False)