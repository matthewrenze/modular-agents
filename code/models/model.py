

class Model:

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.model_version = ""
        self.cached_tokens = 0
        self.input_tokens = 0
        self.reasoning_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self.step_cached_tokens = 0
        self.step_input_tokens = 0
        self.step_reasoning_tokens = 0
        self.step_output_tokens = 0
        self.step_total_tokens = 0
        self.wait_time = 0

    def reset(self) -> None:
        self.cached_tokens = 0
        self.input_tokens = 0
        self.reasoning_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self.step_cached_tokens = 0
        self.step_input_tokens = 0
        self.step_reasoning_tokens = 0
        self.step_output_tokens = 0
        self.step_total_tokens = 0
        self.wait_time = 0

    def reset_step(self) -> None:
        self.step_cached_tokens = 0
        self.step_input_tokens = 0
        self.step_reasoning_tokens = 0
        self.step_output_tokens = 0
        self.step_total_tokens = 0

    def update_tokens(self, cached_tokens, input_tokens, reasoning_tokens, output_tokens, total_tokens):

        # Add marginal tokens
        self.step_cached_tokens += cached_tokens
        self.step_input_tokens += input_tokens
        self.step_reasoning_tokens += reasoning_tokens
        self.step_output_tokens += output_tokens
        self.step_total_tokens += total_tokens

        # Add cumulative tokens
        self.cached_tokens += cached_tokens
        self.input_tokens += input_tokens
        self.reasoning_tokens += reasoning_tokens
        self.output_tokens += output_tokens
        self.total_tokens += total_tokens

    def get_response(self, messages):
        raise NotImplementedError("Subclasses must implement this method")
