from models.model import Model
from states.global_state import GlobalState
from common.parameters import Parameters

class Agent:

    def __init__(self, model, system_prompt: str, params: Parameters):
        self.model = model
        self.system_prompt = system_prompt
        self.params = params
        self.messages = []

    def reset(self):
        pass

    def execute(self, state: GlobalState) -> str:
        pass