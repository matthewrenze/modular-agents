from renderers.renderer_factory import RendererFactory
from params.parameters import Parameters
from agents.agent import Agent
from models.model import Model
from agents.react_k0.react_k0 import ReactK0
from agents.react_k1.react_k1 import ReactK1
from agents.react_kn.react_kn import ReactKn
from agents.tasker.tasker import Tasker
from agents.summarizer.summarizer import Summarizer
from agents.planner.planner import Planner
from agents.memorizer.memorizer import Memorizer
from agents.reasoner.reasoner import Reasoner
from agents.actor.actor import Actor
from agents.reviewer.reviewer import Reviewer
from agents.analyzer.analyzer import Analyzer
from prompts.system_prompt_factory import SystemPromptFactory

class AgentFactory:
    def create(self, subagent: str, params: Parameters, model: Model) -> Agent:

        # Create the renderer
        renderer_factory = RendererFactory()
        renderer = renderer_factory.create()

        # Load the system prompt template
        subagent_folder = subagent.replace("-", "_")
        system_prompt_file_path = f"agents/{subagent_folder}/{subagent}-system-prompt.md"
        with open(system_prompt_file_path, "r") as system_prompt_file:
            system_prompt = system_prompt_file.read()

        # Create the system prompt
        system_prompt_factory = SystemPromptFactory()
        system_prompt = system_prompt_factory.create(params, subagent, system_prompt)

        # Create the appropriate agent
        if subagent == "react-k0":
            return ReactK0(model, renderer, system_prompt, params)

        if subagent == "react-k1":
            return ReactK1(model, renderer, system_prompt, params)

        if subagent == "react-kn":
            return ReactKn(model, renderer, system_prompt, params)

        if subagent == "tasker":
            return Tasker(model, renderer, system_prompt, params)

        if subagent == "summarizer":
            return Summarizer(model, renderer, system_prompt, params)

        if subagent == "planner":
            return Planner(model, renderer, system_prompt, params)

        if subagent == "memorizer":
            return Memorizer(model, renderer, system_prompt, params)

        if subagent == "reasoner":
            return Reasoner(model, renderer, system_prompt, params)

        if subagent == "actor":
            return Actor(model, renderer, system_prompt, params)

        if subagent == "reviewer":
            return Reviewer(model, renderer, system_prompt, params)

        if subagent == "analyzer":
            return Analyzer(model, renderer, system_prompt, params)

        raise ValueError(f"Unknown subagent type: {subagent}")