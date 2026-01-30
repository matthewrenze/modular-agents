from dataclasses import dataclass

@dataclass
class Parameters:
    agent_name: str = ""
    model_name: str = ""
    env_name: str = ""
    eval_name: str = ""
    eval_size: int = 0
    max_steps: int = 0

    # Feature toggles
    use_react: bool = False
    use_tasker: bool = False
    use_reasoner: bool = False
    use_actor: bool = True
    use_summarizer: bool = False