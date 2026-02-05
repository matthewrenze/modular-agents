from models.cost_calculator import CostCalculator

class TestCostCalculator:
    def test_input_cost(self):
        model = "gpt-5"
        cached_tokens = 1_000_000
        input_tokens = 1_000_000
        expected_cost = (0.125 + 1.25)
        calculator = CostCalculator()
        actual_cost = calculator.get_input_cost(model, cached_tokens, input_tokens)
        assert actual_cost == expected_cost

    def test_input_no_cached(self):
        model = "claude-sonnet-4-5"
        cached_tokens = 0
        input_tokens = 1_000_000
        expected_cost = 3.00
        calculator = CostCalculator()
        actual_cost = calculator.get_input_cost(model, cached_tokens, input_tokens)
        assert actual_cost == expected_cost

    def test_output_cost(self):
        model = "gpt-5"
        reasoning_tokens = 1_000_000
        output_tokens = 1_000_000
        expected_cost = (10.00 + 10.00)
        calculator = CostCalculator()
        actual_cost = calculator.get_output_cost(model, reasoning_tokens, output_tokens)
        assert actual_cost == expected_cost

    def test_output_no_reasoning(self):
        model = "claude-sonnet-4-5"
        reasoning_tokens = 0
        output_tokens = 1_000_000
        expected_cost = 15.00
        calculator = CostCalculator()
        actual_cost = calculator.get_output_cost(model, reasoning_tokens, output_tokens)
        assert actual_cost == expected_cost

