from renderers.render import Renderer
from renderers.task.task_renderer import TaskRenderer
from renderers.history.history_renderer import HistoryRenderer
from renderers.memories.memories_renderer import MemoriesRenderer
from renderers.step.step_renderer import StepRenderer
from renderers.environment.env_renderer import EnvRenderer
from renderers.agent.agent_renderer import AgentRenderer

class RendererFactory:

    @staticmethod
    def create():
        task_renderer = TaskRenderer()
        history_renderer = HistoryRenderer()
        memories_renderer = MemoriesRenderer()
        step_renderer = StepRenderer()
        env_renderer = EnvRenderer()
        agent_renderer = AgentRenderer()

        return Renderer(
            task_renderer=task_renderer,
            history_renderer=history_renderer,
            memories_renderer=memories_renderer,
            step_renderer=step_renderer,
            env_renderer=env_renderer,
            agent_renderer=agent_renderer)