class DetailsRow:
    def __init__(self):
        self.step_id = 0
        self.task = ""
        self.feedback = ""
        self.location = ""
        self.description = ""
        self.inventory = ""
        self.score = ""
        self.reward = 0.0
        self.is_done = False
        self.summary = ""
        self.thought = ""
        self.action = ""
        self.error = ""
        self.cached_tokens = 0
        self.input_tokens = 0
        self.reasoning_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0