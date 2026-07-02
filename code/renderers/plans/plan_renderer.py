class PlanRenderer:
    def render(self, plan: str) -> str:

        if not plan:
            return "Plan: N/A\n"

        output = "Plan:\n"
        for step in plan.strip().split("\n"):
            output += f"  {step}\n"
        return output