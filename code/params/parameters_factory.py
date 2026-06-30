from params.parameters import Parameters

class ParametersFactory:
    def create(self, split_name: str, model_name: str, agent_name: str, env_name: str, eval_name: str, eval_size: int = 0, episode_id: int = 0):

        # Handle invalid split name
        if split_name not in ["train", "test"]:
            raise ValueError("Split name must be 'train' or 'test'.")

        # Set parameters
        parameters = Parameters(
            split_name=split_name,
            model_name=model_name,
            agent_name=agent_name,
            env_name=env_name,
            eval_name=eval_name,
            eval_size=eval_size,
            episode_id=episode_id,
            max_steps=0)

        # Create the react-k0 agent
        if agent_name.startswith("react-k0"):
            parameters = self.minus_all(parameters)
            parameters.use_react_k0 = True
            return parameters

        # Create the react-k1 agent
        if agent_name.startswith("react-k1"):
            parameters = self.minus_all(parameters)
            parameters.use_react_k1 = True
            return parameters

        # Create the react-kn agent
        if agent_name.startswith("react-kn"):
            parameters = self.minus_all(parameters)
            parameters.use_react_kn = True
            return parameters

        # Create modular-base agent
        if agent_name.startswith("modular-base"):
            parameters = self.minus_all(parameters)
            parameters.use_reasoner = True
            parameters.use_actor = True
            return parameters

        # Create modular-full agent
        if agent_name.startswith("modular-full"):
            parameters = self.plus_all(parameters)
            return parameters

        # Create baseline-plus agents
        if agent_name.startswith("plus-"):
            parameters = self.minus_all(parameters)
            if "summarizer" in agent_name:
                parameters.use_summarizer = True
            elif "planner" in agent_name:
                parameters.use_planner = True
            elif "memorizer" in agent_name:
                parameters.use_memorizer = True
            else:
                raise ValueError(f"Agent name '{agent_name}' names no known module.")
            parameters.use_reasoner = True
            parameters.use_actor = True
            return parameters

        # Create topline-minus agents
        if agent_name.startswith("minus-"):
            parameters = self.plus_all(parameters)
            if "summarizer" in agent_name:
                parameters.use_summarizer = False
            elif "planner" in agent_name:
                parameters.use_planner = False
            elif "memorizer" in agent_name:
                parameters.use_memorizer = False
            else:
                raise ValueError(f"Agent name '{agent_name}' names no known module.")
            parameters.use_actor = True
            return parameters

        raise ValueError("Agent name not recognized.")

    @staticmethod
    def plus_all(parameters: Parameters) -> Parameters:
        parameters.use_summarizer = True
        parameters.use_planner = True
        parameters.use_memorizer = True
        parameters.use_reasoner = True
        parameters.use_actor = True
        return parameters

    @staticmethod
    def minus_all(parameters: Parameters) -> Parameters:
        parameters.use_summarizer = False
        parameters.use_planner = False
        parameters.use_memorizer = False
        parameters.use_reasoner = False
        parameters.use_actor = False
        return parameters

