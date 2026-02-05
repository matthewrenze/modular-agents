# plan.py
from typing import TypeAlias, List
from plans.plan_step import PlanStep

# Note: This allows me to use "Plan" instead of "List[PlanStep]"
Plan: TypeAlias = List[PlanStep]
