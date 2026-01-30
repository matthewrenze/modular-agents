from agents.summarizer.summarizer import Summarizer
from common.parameters import Parameters
from agents.agent import Agent
from models.model import Model
from agents.react.react_agent import ReactAgent
from agents.actor.actor_agent import ActorAgent
from agents.tasker.tasker_agent import TaskerAgent
from agents.reasoner.reasoner_agent import ReasonerAgent
from agents.reviewer.reviewer import Reviewer
from prompts.system_prompt_factory import SystemPromptFactory

class AgentFactory:
    def create(self, subagent: str, params: Parameters, model: Model) -> Agent:

        # Load the system prompt template
        system_prompt_file_path = f"agents/{subagent}/{subagent}-system-prompt.md"
        with open(system_prompt_file_path, "r") as system_prompt_file:
            system_prompt = system_prompt_file.read()

        # Create the system prompt
        system_prompt_factory = SystemPromptFactory()
        system_prompt = system_prompt_factory.create(params, subagent, system_prompt)

        # Create the appropriate agent
        if subagent == "react":
            return ReactAgent(model, system_prompt, params)

        if subagent == "tasker":
            return TaskerAgent(model, system_prompt, params)

        if subagent == "reasoner":
            return ReasonerAgent(model, system_prompt, params)

        if subagent == "actor":
            return ActorAgent(model, system_prompt, params)

        if subagent == "summarizer":
            return Summarizer(model, system_prompt, params)

        if subagent == "reviewer":
            return Reviewer(model, system_prompt, params)

        raise ValueError(f"Unknown subagent type: {subagent}")