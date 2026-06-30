from params.parameters import Parameters
from results.results_manager import ResultsManager

class TestResultsManager:

    def make_params(self, episode_id):
        return Parameters(
            split_name="test",
            model_name="model",
            agent_name="agent",
            eval_name="eval",
            episode_id=episode_id)

    def make_manager(self, tmp_path):
        manager = ResultsManager()
        manager.folder_path = str(tmp_path)
        return manager

    def save_episode(self, manager, episode_id, reward=0.0):
        params = self.make_params(episode_id)
        row = manager.create(params)
        row.episode = episode_id
        row.reward = reward
        manager.save_row(params, row)

    def test_save_row_sorts_by_episode(self, tmp_path):
        manager = self.make_manager(tmp_path)
        for episode_id in [3, 1, 2]:
            self.save_episode(manager, episode_id)
        manager.load(self.make_params(1))
        assert manager.get_table()["episode"].tolist() == [1, 2, 3]

    def test_save_row_replaces_existing_episode(self, tmp_path):
        manager = self.make_manager(tmp_path)
        self.save_episode(manager, 1, reward=0.0)
        self.save_episode(manager, 1, reward=1.0)
        manager.load(self.make_params(1))
        table = manager.get_table()
        assert len(table) == 1
        assert table["reward"].iloc[0] == 1.0

    def test_exists(self, tmp_path):
        manager = self.make_manager(tmp_path)
        assert not manager.exists(self.make_params(1))
        self.save_episode(manager, 1)
        assert manager.exists(self.make_params(1))
        assert not manager.exists(self.make_params(2))
