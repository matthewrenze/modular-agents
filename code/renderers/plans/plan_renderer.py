from plans.plan import Plan

class PlanRenderer:
    def render(self, plan: Plan) -> str:

        if not plan:
            return "Plan: N/A.\n"

        output = "Plan:\n"
        for step in plan:
            status_tag = "X" if step.status == "done" else " "
            output += f"  {step.id} [{status_tag}] {step.label}\n"
        return output