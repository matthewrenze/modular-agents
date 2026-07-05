from artifacts.artifacts import Artifacts

class ReviewReader:
    def __init__(self, artifacts: Artifacts):
        self.artifacts = artifacts

    def read(self, params) -> str:

        # Create the file path
        folder_path = self.artifacts.get_episode_folder_path(params)
        file_name = self.artifacts.get_file_name(params, "review.txt")
        file_path = f"{folder_path}/{file_name}"

        # Read the review
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()
        return text
