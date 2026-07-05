from artifacts.artifacts import Artifacts
from params.parameters import Parameters

class ReviewWriter:
    def __init__(self, artifacts: Artifacts):
        self.artifacts = artifacts

    def write(self, params: Parameters, review: str):

        # Create the file path
        folder_path = self.artifacts.create_episode(params)
        file_name = self.artifacts.get_file_name(params, "review.txt")
        file_path = f"{folder_path}/{file_name}"

        # Write the review
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(review)
