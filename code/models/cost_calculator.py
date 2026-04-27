class CostCalculator:
    def __init__(self):
        # Note: All costs are in USD per million tokens
        self.cost_map = {
            "claude-sonnet-4-6": {"cached": 0.30, "input": 3.00, "output": 15.00},
            "claude-opus-4-6": {"cached": 0.50, "input": 5.00, "output": 25.00},
            "deepseek-v4-pro": {"cached": 0.15, "input": 1.74, "output": 3.48},
            "gemini-3.1-pro-preview": {"cached": 0.20, "input": 2.00, "output": 12.00},
            "glm-5-fast": {"cached": 0.20, "input": 1.00, "output": 3.20},
            "glm-5.1": {"cached": 0.26, "input": 1.40, "output": 4.40},
            "gpt-5.2": {"cached": 0.175, "input": 1.75, "output": 14.00},
            "gpt-5.4-mini": {"cached": 0.075, "input": 0.75, "output": 4.50},
            "gpt-5.4": {"cached": 0.25, "input": 2.50, "output": 15.00},
            "gpt-5.5": {"cached": 0.50, "input": 5.00, "output": 30.00},
            "kimi-k2.5" : {"cached": 0.10, "input": 0.60, "output": 3.00},
            "kimi-k2.5-turbo": {"cached": 0.10, "input": 0.60, "output": 3.00},
            "kimi-k2.6" : {"cached": 0.16, "input": 0.95, "output": 4.00},
            "qwen3.6-plus" : {"cached": 0.10, "input": 0.50, "output": 3.00},
        }

    def get_input_cost(self, model, cached_tokens, input_tokens):
        cached_unit_cost = self.cost_map[model].get("cached", 0)
        cached_cost = cached_tokens / 1_000_000 * cached_unit_cost
        input_unit_cost = self.cost_map[model]["input"]
        input_cost = input_tokens / 1_000_000 * input_unit_cost
        input_total_cost = cached_cost + input_cost
        return input_total_cost

    def get_output_cost(self, model, reasoning_tokens, output_tokens):
        output_unit_cost = self.cost_map[model]["output"]
        reasoning_cost = reasoning_tokens / 1_000_000 * output_unit_cost
        output_cost = output_tokens / 1_000_000 * output_unit_cost
        total_output_cost = reasoning_cost + output_cost
        return total_output_cost




