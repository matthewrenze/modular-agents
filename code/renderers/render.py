from renderers.task.task_renderer import TaskRenderer
from renderers.history.history_renderer import HistoryRenderer
from renderers.memories.memories_renderer import MemoriesRenderer
from renderers.step.step_renderer import StepRenderer
from renderers.environment.env_renderer import EnvRenderer
from renderers.agent.agent_renderer import AgentRenderer
from states.task_state import TaskState
from states.step_state import StepState
from states.env_state import EnvState
from states.agent_state import AgentState


class Renderer:
    def __init__(self,
            task_renderer: TaskRenderer,
            history_renderer: HistoryRenderer,
            memories_renderer: MemoriesRenderer,
            step_renderer: StepRenderer,
            env_renderer: EnvRenderer,
            agent_renderer: AgentRenderer):
        self.task_renderer = task_renderer
        self.history_renderer = history_renderer
        self.memories_renderer = memories_renderer
        self.step_renderer = step_renderer
        self.env_renderer = env_renderer
        self.agent_renderer = agent_renderer

    def render_task(self, task_state: TaskState) -> str:
        return self.task_renderer.render(task_state)

    def render_history(self, step_history: list) -> str:
        return self.history_renderer.render(step_history)

    def render_memories(self, memories: dict) -> str:
        return self.memories_renderer.render(memories)

    def render_step(self, step_state: StepState, task_state: TaskState) -> str:
        return self.step_renderer.render(step_state, task_state)

    def render_env(self, env_state: EnvState, task_state: TaskState) -> str:
        return self.env_renderer.render(env_state, task_state)

    def render_agent(self, agent_state: AgentState) -> str:
        return self.agent_renderer.render(agent_state)

    def render_memory_items(self, memory: str) -> str:
        return self.agent_renderer.render_memory_items(memory)

