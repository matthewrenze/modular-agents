import yaml
from states.global_state import GlobalState


class StateReader:
    def read(self, file_path: str) -> GlobalState:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return GlobalState.model_validate(data)