from common.parameters import Parameters
from agents.agent import Agent
from models.model import Model
from agents.react.react_agent import ReactAgent
from agents.react_k1.react_agent import ReactAgentK1
from agents.tasker.tasker import Tasker
from agents.summarizer.summarizer import Summarizer
from agents.memorizer.memorizer import Memorizer
from agents.reasoner.reasoner import Reasoner
from agents.actor.actor import Actor
from agents.reviewer.reviewer import Reviewer
from prompts.system_prompt_factory import SystemPromptFactory

class AgentFactory:
    def create(self, subagent: str, params: Parameters, model: Model) -> Agent:

        # Load the system prompt template
        subagent_folder = subagent.replace("-", "_")
        system_prompt_file_path = f"agents/{subagent_folder}/{subagent}-system-prompt.md"
        with open(system_prompt_file_path, "r") as system_prompt_file:
            system_prompt = system_prompt_file.read()

        # Create the system prompt
        system_prompt_factory = SystemPromptFactory()
        system_prompt = system_prompt_factory.create(params, subagent, system_prompt)

        # Create the appropriate agent
        if subagent == "react":
            return ReactAgent(model, system_prompt, params)

        if subagent == "react-k1":
            return ReactAgentK1(model, system_prompt, params)

        if subagent == "tasker":
            return Tasker(model, system_prompt, params)

        if subagent == "summarizer":
            return Summarizer(model, system_prompt, params)

        if subagent == "memorizer":
            return Memorizer(model, system_prompt, params)

        if subagent == "reasoner":
            return Reasoner(model, system_prompt, params)

        if subagent == "actor":
            return Actor(model, system_prompt, params)

        if subagent == "reviewer":
            return Reviewer(model, system_prompt, params)

        raise ValueError(f"Unknown subagent type: {subagent}")