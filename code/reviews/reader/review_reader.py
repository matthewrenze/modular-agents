
class ReviewReader:
    def read(self, params, episode_id: int) -> str:

        # Create the file path
        folder_path = f"../data/artifacts/{params.version}/{params.split_name}/{params.model_name}/{params.agent_name}/{params.eval_name}/episode-{episode_id}"
        file_name = f"{params.version} - {params.split_name} - {params.model_name} - {params.agent_name} - {params.eval_name} - episode-{episode_id} - review.txt"
        file_path = f"{folder_path}/{file_name}"

        # Read the review
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()
        return text




