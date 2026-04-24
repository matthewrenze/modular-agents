import os
from params.parameters import Parameters
from renderers.render import Renderer
from states.task_state import TaskState
from states.step_state import StepState
from states.env_state import EnvState
from states.agent_state import AgentState

# Define the ANSI colors
BOLD_WHITE = "\033[97m"
WHITE = "\033[38;5;250m"
YELLOW = "\033[93m"
ORANGE = "\033[38;5;208m"
RED = "\033[91m"
RESET = "\033[0m"

class Log:
    def __init__(self, renderer: Renderer, params: Parameters, episode_id):
        self.renderer = renderer
        folder_path = f"../data/artifacts/{params.split_name}/{params.model_name}/{params.agent_name}/{params.eval_name}/episode-{episode_id}"
        file_name = f"{params.split_name} - {params.model_name} - {params.agent_name} - {params.eval_name} - episode-{episode_id} - log.txt"
        file_path = f"{folder_path}/{file_name}"
        os.makedirs(folder_path, exist_ok=True)
        self.file = open(file_path, "w", encoding="utf-8", newline="\n")

    def head(self, text):
        self.file.write(f"{text}\n")
        print(f"{BOLD_WHITE}{text}{RESET}")

    def info(self, text):
        self.file.write(f"{text}\n")
        print(f"{WHITE}{text}{RESET}")

    def debug(self, text):
        self.file.write(f"Debug: {text}\n")
        print(f"{YELLOW}Debug: {text}{RESET}")

    def warning(self, warning):
        self.file.write(f"Warning: {warning}\n")
        print(f"{ORANGE}Warning: {warning}{RESET}")

    def error(self, error):
        self.file.write(f"Error: {error}\n")
        print(f"{RED}Error: {error}{RESET}")

    def raw(self, text):
        text = text.lstrip().rstrip() + "\n"
        self.file.write(text)
        print(text)

    def task(self, task_state: TaskState):
        task_text = self.renderer.render_task(task_state)
        self.raw(task_text)

    def step(self, step_index: StepState, task_state: TaskState):
        step_text = self.renderer.render_step(step_index, task_state)
        self.raw(step_text)

    def history(self, step_history: list[StepState]):
        history_text = self.renderer.render_history(step_history)
        self.raw(history_text)

    def plan(self, plan: str):
        plan_text = self.renderer.render_plan(plan)
        self.raw(plan_text)

    def memories(self, memories: dict[str, str]):
        memories_text = self.renderer.render_memories(memories)
        self.raw(memories_text)

    def env(self, env_state: EnvState, task_state: TaskState):
        env_text = self.renderer.render_env(env_state, task_state)
        self.raw(env_text)

    def agent(self, agent_state: AgentState):
        agent_text = self.renderer.render_agent(agent_state, True)
        self.raw(agent_text)

    def close(self):
        self.file.flush()
        self.file.close()