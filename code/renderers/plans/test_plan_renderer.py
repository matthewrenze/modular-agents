from renderers.plans.plan_renderer import PlanRenderer
from plans.plan import Plan
from plans.plan_step import PlanStep

class TestPlanRenderer:

    def test_render(self):
        plan = [
            PlanStep(id=1, status="done", label="step 1"),
            PlanStep(id=2, status="todo", label="step 2")]
        expected = (
            "Plan:\n"
            "  1 [X] step 1\n"
            "  2 [ ] step 2\n")

        renderer = PlanRenderer()
        actual = renderer.render(plan)

        assert actual == expected

    def test_render_empty(self):
        plan = []
        expected = "Plan: N/A.\n"

        renderer = PlanRenderer()
        actual = renderer.render(plan)

        assert actual == expected