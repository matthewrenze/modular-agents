from models.cost_calculator import CostCalculator

class TestCostCalculator:
    def test_input_cost(self):
        model = "gpt-5.2"
        cached_tokens = 1_000_000
        input_tokens = 1_000_000
        expected_cost = (0.175 + 1.75)
        calculator = CostCalculator()
        actual_cost = calculator.get_input_cost(model, cached_tokens, input_tokens)
        assert actual_cost == expected_cost

    def test_input_no_cached(self):
        model = "claude-sonnet-4-6"
        cached_tokens = 0
        input_tokens = 1_000_000
        expected_cost = 3.00
        calculator = CostCalculator()
        actual_cost = calculator.get_input_cost(model, cached_tokens, input_tokens)
        assert actual_cost == expected_cost

    def test_output_cost(self):
        model = "gpt-5.2"
        reasoning_tokens = 1_000_000
        output_tokens = 1_000_000
        expected_cost = (14.00 + 14.00)
        calculator = CostCalculator()
        actual_cost = calculator.get_output_cost(model, reasoning_tokens, output_tokens)
        assert actual_cost == expected_cost

    def test_output_no_reasoning(self):
        model = "claude-sonnet-4-6"
        reasoning_tokens = 0
        output_tokens = 1_000_000
        expected_cost = 15.00
        calculator = CostCalculator()
        actual_cost = calculator.get_output_cost(model, reasoning_tokens, output_tokens)
        assert actual_cost == expected_cost

    def test_gpt_5_6_sol_costs(self):
        model = "gpt-5.6-sol"
        calculator = CostCalculator()
        input_cost = calculator.get_input_cost(model, 1_000_000, 1_000_000)
        output_cost = calculator.get_output_cost(model, 0, 1_000_000)
        assert input_cost == (0.50 + 5.00)
        assert output_cost == 30.00

    def test_claude_fable_5_costs(self):
        model = "claude-fable-5"
        calculator = CostCalculator()
        input_cost = calculator.get_input_cost(model, 1_000_000, 1_000_000)
        output_cost = calculator.get_output_cost(model, 0, 1_000_000)
        assert input_cost == (1.00 + 10.00)
        assert output_cost == 50.00

