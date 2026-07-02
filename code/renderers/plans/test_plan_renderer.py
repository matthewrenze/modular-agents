from renderers.plans.plan_renderer import PlanRenderer

class TestPlanRenderer:

    def test_render(self):
        plan = (
            "- [x] step 1\n"
            "- [ ] step 2\n")
        expected = (
            "Plan:\n"
            "  - [x] step 1\n"
            "  - [ ] step 2\n")

        renderer = PlanRenderer()
        actual = renderer.render(plan)

        assert actual == expected

    def test_render_empty(self):
        plan = ""
        expected = "Plan: N/A\n"

        renderer = PlanRenderer()
        actual = renderer.render(plan)

        assert actual == expected