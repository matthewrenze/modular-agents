
class ReviewReader:
    def read(self, params, episode_id: int) -> str:

        # Create the file path
        folder_path = f"../data/reviews/{params.model_name} - {params.agent_name} - {params.eval_name}"
        file_path = f"{folder_path}/{episode_id}.txt"

        # Read the review
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()
        return text




