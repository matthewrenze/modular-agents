from models.model import Model
from states.global_state import GlobalState
from params.parameters import Parameters
from renderers.render import Renderer

class Agent:

    def __init__(self, model, renderer: Renderer, system_prompt: str, params: Parameters):
        self.model = model
        self.renderer = renderer
        self.system_prompt = system_prompt
        self.params = params
        self.messages = []

    def reset(self):
        pass

    def execute(self, state: GlobalState) -> str:
        pass