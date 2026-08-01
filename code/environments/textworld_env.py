import re
import textworld.gym
from states.task_state import TaskState
from states.env_state import EnvState

import json

class TextWorldEnv:
    def __init__(self, params, evals):
        self.params = params
        self.evals = evals
        self.env = None
        self.episode = None
        self.episode_id = 0
        self.step_index = 0

    def reset(self, episode_id: int) -> tuple[TaskState, EnvState]:
        self.episode_id = episode_id
        self.episode = self.evals.iloc[episode_id - 1].to_dict()
        game_file_path = self.episode["file_path"]
        json_file_path = game_file_path.replace(".ulx", ".json")
        json_data = json.load(open(json_file_path))

        # Set the env info (what info the player has access to)
        # NOTE: admissible_commands is never read by the harness and computing it
        # costs 10-15s/step late in tw-long-cook games, so it is not requested
        env_infos = textworld.EnvInfos(
            objective=True,
            description=True,
            inventory=True,
            feedback=True,
            max_score=True,)

        # Register the game
        env_id = textworld.gym.register_game(
            gamefile=game_file_path,
            request_infos=env_infos,
            max_episode_steps=self.params.max_steps)

        # Close the previous environment if it exists
        # NOTE: This is to fix the "GameNotRunningError" that occurs during many parallel evals
        if self.env is not None:
            self.env.close()
            self.env = None

        # Create the environment
        self.env = textworld.gym.make(env_id)

        # Reset the environment
        _, infos = self.env.reset()

        # Reset the properties
        self.step_index = 0

        # Get the state info
        task = infos["objective"].strip()
        description = infos["description"].strip()
        location = self.get_location(description)
        inventory = infos["inventory"].strip()
        num_items = self.get_items(inventory)
        max_items = self.get_max_items(json_data)
        score = 0
        max_score = infos["max_score"]

        # Clean up the text
        description = self.remove_location(description)
        description = self.clean_text(description)

        # Create the task state
        task_state = TaskState(
            task=task,
            step_id=0,
            max_steps=self.params.max_steps,
            max_items=max_items,
            max_score=max_score,
            max_reward=1.0,
            success=False)

        # Create the state
        step_state = EnvState(
            feedback="",
            location=location,
            description=description,
            inventory=inventory,
            items=num_items,
            score=score,
            reward=0,
            is_done=False)

        return task_state, step_state

    def render(self):
        self.env.render()

    def step(self, action: str) -> EnvState:
        # HACK: Fix the "take <object> from floor" issue
        if action.startswith("take "):
            action = action.replace(" from floor", "")

        # Step the environment
        _, score, is_done, infos = self.env.step(action)

        # Get the state info
        feedback = infos["feedback"].strip()
        description = infos["description"].strip()
        location = self.get_location(description)
        inventory = infos["inventory"].strip()
        items = self.get_items(inventory)
        max_score = infos["max_score"]
        reward = score / max_score

        # Clean up the text
        feedback = self.remove_location(feedback)
        feedback = self.clean_text(feedback)
        description = self.remove_location(description)
        description = self.clean_text(description)

        # Handle the quit action
        if action == "quit":
            is_done = True

        # Create the state
        state = EnvState(
            feedback=feedback,
            location=location,
            description=description,
            inventory=inventory,
            items=items,
            score=score,
            reward=reward,
            is_done=is_done)

        # Increment step index
        self.step_index += 1

        return state

    @staticmethod
    def get_location(description: str) -> str:
        match = re.search(r'-= (.*?) =-', description)
        return match.group(1).strip()

    @staticmethod
    def remove_location(description: str) -> str:
        return re.sub(r'-= (.*?) =-', '', description).strip()

    @staticmethod
    def clean_text(text):
        text = re.sub(r'\n+', '\n', text)
        text = re.sub('\n', ' ', text)
        text = re.sub(r'(?<!^)\s+', ' ', text)
        return text

    @staticmethod
    def get_items(inventory: str) -> int:
        if inventory == "You are carrying nothing.":
            return 0

        if inventory.startswith("You are carrying:") \
                and "and" not in inventory:
            return 1

        return len(inventory.split(",")) + 1

    @staticmethod
    def get_max_items(game_data: str) -> int:
        metadata = game_data.get("metadata", {})
        settings = metadata.get("settings", {})
        if settings.get("drop", False):
            return int(settings.get("recipe", 0))
        return 10


