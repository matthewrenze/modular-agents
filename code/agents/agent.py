from models.model import Model
from states.global_state import GlobalState

class Agent:

    def __init__(self, model, system_prompt: str):
        self.model = model
        self.system_prompt = system_prompt
        self.messages = []

    def reset(self):
        pass

    def execute(self, state: GlobalState) -> str:
        pass