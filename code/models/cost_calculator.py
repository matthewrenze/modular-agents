from thinc.tests.layers.test_softmax import inputs


class CostCalculator:
    def __init__(self):
        # Note: All costs are in USD per million tokens
        self.cost_map = {
            "claude-sonnet-4-0": {"input": 3.00, "output": 15.00},
            "claude-opus-4-1": {"input": 15.00, "output": 75.00},
            "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
            "deepseek-r1": {"input": 0.56, "output": 1.68},
            "deepseek-v3": {"input": 0.56, "output": 1.68},
            "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
            "gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40},
            "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
            "gemini-3-pro-preview": {"input": 2.00, "output": 12.00},
            "gpt-4.1": {"cached": 0.50, "input": 3.00, "output": 12.00},
            "gpt-4.1-mini": {"cached": 0.10, "input": 0.80, "output": 3.20},
            "gpt-5": {"cached": 0.125, "input": 1.25, "output": 10.00},
            "gpt-5-mini": {"cached": 0.025, "input": 0.25, "output": 2.00},
            "gpt-5.1": {"cached": 0.125, "input": 1.25, "output": 10.00},
            "gpt-5.2": {"cached": 0.175, "input": 1.75, "output": 14.00},
            "grok-3": {"input": 3.00, "output": 15.00},
            "grok-3-mini": {"input": 0.30, "output": 0.50},
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




