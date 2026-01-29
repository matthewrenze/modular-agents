from common.parameters import Parameters

class ParametersFactory:
    def create(self, agent_name: str, model_name: str, env_name: str, eval_name: str, eval_size: int):

        # Set parameters
        parameters = Parameters(
            agent_name=agent_name,
            model_name=model_name,
            env_name=env_name,
            eval_name=eval_name,
            eval_size=eval_size,
            max_steps=0)

        # Create the react agent
        if agent_name == "react":
            parameters = self.minus_all(parameters)
            parameters.use_react = True
            return parameters

        # Create baseline agent
        if agent_name == "baseline":
            parameters = self.minus_all(parameters)
            parameters.use_actor = True
            return parameters

        # Create topline agent
        if agent_name == "topline":
            parameters = self.plus_all(parameters)
            return parameters

        # Create baseline-plus agents
        if agent_name.startswith("plus-"):
            parameters = self.minus_all(parameters)
            if "tasker" in agent_name:
                parameters.use_tasker = True
            if "reasoner" in agent_name:
                parameters.use_reasoner = True
            return parameters

        # Create topline-minus agents
        if agent_name.startswith("minus-"):
            parameters = self.plus_all(parameters)
            if "tasker" in agent_name:
                parameters.use_tasker = False
            if "reasoner" in agent_name:
                parameters.use_reasoner = False
            return parameters

    @staticmethod
    def plus_all(parameters: Parameters) -> Parameters:
        parameters.use_tasker = True
        parameters.use_actor = True
        parameters.use_reasoner = True
        return parameters

    @staticmethod
    def minus_all(parameters: Parameters) -> Parameters:
        parameters.use_tasker = False
        parameters.use_actor = False
        parameters.use_reasoner = False
        return parameters

