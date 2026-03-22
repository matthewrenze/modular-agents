import os
import yaml
from params.parameters import Parameters
from states.global_state import GlobalState


class StateWriter:

    def write(self, state: GlobalState, params: Parameters, episode_id: int):

        # Create the folder
        folder_path = f"../data/artifacts/{params.model_name}/{params.agent_name}/{params.eval_name}/episode-{episode_id}"
        os.makedirs(folder_path, exist_ok=True)

        # Deep copy the state
        data = state.model_dump(mode="python")

        # Wrap plan as a YAML string literal
        # Note: to render block literal "|"
        for step in data.get("step_history", []):
            agent = step.get("agent_state") or {}
            plan = agent.get("plan")
            if isinstance(plan, str) and "\n" in plan:
                agent["plan"] = LiteralStr(plan)

        # Wrap memory as a YAML string literal
        for step in data.get("step_history", []):
            agent = step.get("agent_state") or {}
            mem = agent.get("memory")
            if isinstance(mem, str) and "\n" in mem:
                agent["memory"] = LiteralStr(mem)

        # Write the file
        file_name = f"{params.model_name} - {params.agent_name} - {params.eval_name} - episode-{episode_id} - state.yaml"
        file_path = f"{folder_path}/{file_name}"
        with open(file_path, "w", encoding="utf-8") as file:
            yaml.safe_dump(
                data,
                file,
                sort_keys=False,
                default_flow_style=False,
                allow_unicode=True)


class LiteralStr(str):
    pass

def literal_str_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

yaml.add_representer(LiteralStr, literal_str_representer, Dumper=yaml.SafeDumper)
