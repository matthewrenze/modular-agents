import os
from artifacts.artifacts import Artifacts
from params.parameters import Parameters


class TestArtifacts:

    def make_params(self):
        return Parameters(
            version="version",
            split_name="split",
            model_name="model",
            agent_name="agent",
            eval_name="eval",
            episode_id=7)

    def test_get_agent_folder_path(self):
        path = Artifacts().get_agent_folder_path(self.make_params())
        assert path == "../data/artifacts/version/split/model/agent"

    def test_get_eval_folder_path(self):
        path = Artifacts().get_eval_folder_path(self.make_params())
        assert path == "../data/artifacts/version/split/model/agent/eval"

    def test_get_episode_folder_path(self):
        path = Artifacts().get_episode_folder_path(self.make_params())
        assert path == "../data/artifacts/version/split/model/agent/eval/episode-7"

    def test_get_agent_file_name(self):
        name = Artifacts().get_agent_file_name(self.make_params(), "analysis.txt")
        assert name == "version - split - model - agent - analysis.txt"

    def test_get_eval_file_name(self):
        name = Artifacts().get_eval_file_name(self.make_params(), "results.csv")
        assert name == "version - split - model - agent - eval - results.csv"

    def test_get_file_name(self):
        name = Artifacts().get_file_name(self.make_params(), "log.txt")
        assert name == "version - split - model - agent - eval - episode-7 - log.txt"

    def test_create_episode(self, tmp_path):
        artifacts = Artifacts()
        artifacts.folder_path = str(tmp_path)
        params = self.make_params()
        folder_path = artifacts.create_episode(params)
        assert folder_path == artifacts.get_episode_folder_path(params)
        assert os.path.isdir(folder_path)

    def test_delete_episode(self, tmp_path):
        artifacts = Artifacts()
        artifacts.folder_path = str(tmp_path)
        params = self.make_params()
        folder_path = artifacts.get_episode_folder_path(params)
        os.makedirs(folder_path)
        with open(f"{folder_path}/file.txt", "w") as file:
            file.write("content")
        artifacts.delete_episode(params)
        assert not os.path.exists(folder_path)

    def test_delete_episode_missing_folder(self, tmp_path):
        artifacts = Artifacts()
        artifacts.folder_path = str(tmp_path)
        artifacts.delete_episode(self.make_params())
