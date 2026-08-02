from dataclasses import dataclass

@dataclass
class Parameters:
    version: str = ""
    split_name: str = ""
    model_name: str = ""
    agent_name: str = ""
    env_name: str = ""
    eval_name: str = ""
    eval_size: int = 0
    episode_id: int = 0
    max_steps: int = 0

    # Step-history window: the number of previous steps in context,
    # in addition to the current step (k=n is stored as sys.maxsize)
    k: int = 1

    # Feature toggles
    use_react_k0: bool = False
    use_react_k: bool = False
    use_react_kn: bool = False
    use_summarizer: bool = False
    use_planner: bool = False
    use_memorizer: bool = False
    use_reasoner: bool = False
    use_actor: bool = True