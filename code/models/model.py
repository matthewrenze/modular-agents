

class Model:

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.cached_tokens = 0
        self.input_tokens = 0
        self.reasoning_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0

    def reset(self) -> None:
        self.cached_tokens = 0
        self.input_tokens = 0
        self.reasoning_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0

    def get_response(self, messages):
        raise NotImplementedError("Subclasses must implement this method")
