import os
import re
import pandas as pd
from artifacts.artifacts import Artifacts
from params.parameters import Parameters
from states.reader.state_reader import StateReader
from interp.episode_extract import EpisodeExtract

class EpisodeReader:
    def __init__(self, artifacts: Artifacts, state_reader: StateReader):
        self.artifacts = artifacts
        self.state_reader = state_reader

    def read(self, params: Parameters, message_steps: int = 2) -> EpisodeExtract:
        folder_path = self.artifacts.get_episode_folder_path(params)

        # Read the final global state (plan, memories, step history)
        state_path = f"{folder_path}/{self.artifacts.get_file_name(params, 'state.yaml')}"
        state = self.state_reader.read(state_path)

        # Read the per-step details (agent-authored columns + env columns)
        details_path = f"{folder_path}/{self.artifacts.get_file_name(params, 'details.csv')}"
        details = pd.read_csv(details_path, keep_default_na=False)

        # Read the raw module messages for the last N steps
        last_messages = self.read_last_messages(folder_path, message_steps)

        return EpisodeExtract(params=params, state=state, details=details, last_messages=last_messages)

    def read_last_messages(self, folder_path: str, message_steps: int) -> dict:
        messages_path = f"{folder_path}/messages"

        # Index the per-step module message files (step 0 system prompts don't match)
        pattern = re.compile(r"step-(\d+) - ([a-z0-9_]+)\.md$")
        files = {}
        for file_name in os.listdir(messages_path):
            match = pattern.search(file_name)
            if match:
                step_id, module = int(match.group(1)), match.group(2)
                files.setdefault(step_id, {})[module] = file_name

        # Read the module messages for the last N steps
        last_messages = {}
        for step_id in sorted(files)[-message_steps:]:
            last_messages[step_id] = {}
            for module, file_name in files[step_id].items():
                with open(f"{messages_path}/{file_name}", "r", encoding="utf-8") as f:
                    last_messages[step_id][module] = f.read()
        return last_messages
