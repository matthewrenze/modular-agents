# plan_manager.py

import re
from typing import Optional

from plans.plan import Plan
from plans.plan_step import PlanStep


class PlanManager:
    def __init__(self):
        self._next_temp_id = -1

    def execute(self, plan: Plan, operations: str) -> Plan:
        lines = [ln.strip() for ln in operations.splitlines() if ln.strip()]

        for line in lines:
            plan = self._execute_line(plan, line)

        return self._renumber(plan)

    def _execute_line(self, plan: Plan, line: str) -> Plan:

        if line.startswith("add:"):
            return self._execute_add(plan, line)

        if line.startswith("insert:"):
            return self._execute_insert(plan, line)

        if line.startswith("update:"):
            return self._execute_update(plan, line)

        if line.startswith("delete:"):
            return self._execute_delete(plan, line)

        if line.startswith("mark:"):
            return self._execute_mark(plan, line)

        return plan  # unknown op -> no-op (or raise)

    def _execute_add(self, plan: Plan, line: str) -> Plan:
        pattern = r"^add:\s*(.+)$"
        match = re.match(pattern, line, flags=re.IGNORECASE)
        if not match:
            return plan

        label = match.group(1).strip()
        plan_step = PlanStep(id=self._alloc_temp_id(), status="todo", label=label)
        plan.append(plan_step)
        return plan

    def _execute_insert(self, plan: Plan, line: str) -> Plan:
        pattern = r"^insert:\s*(\d+)\s*=\s*(.+)$"
        match = re.match(pattern, line, flags=re.IGNORECASE)
        if not match:
            return plan

        target_id = int(match.group(1))
        label = match.group(2).strip()

        idx = self._find_index(plan, target_id)
        if idx is not None:
            plan_step = PlanStep(id=self._alloc_temp_id(), status="todo", label=label)
            plan.insert(idx, plan_step)
        return plan

    def _execute_update(self, plan: Plan, line: str) -> Plan:
        pattern = r"^update:\s*(\d+)\s*=\s*(.+)$"
        match = re.match(pattern, line, flags=re.IGNORECASE)
        if not match:
            return plan

        target_id = int(match.group(1))
        label = match.group(2).strip()

        step = self._find_step(plan, target_id)
        if step is not None:
            step.label = label
        return plan

    def _execute_delete(self, plan: Plan, line: str) -> Plan:
        pattern = r"^delete:\s*(\d+)\s*$"
        match = re.match(pattern, line, flags=re.IGNORECASE)
        if not match:
            return plan

        target_id = int(match.group(1))
        idx = self._find_index(plan, target_id)

        if idx is not None:
            plan.pop(idx)
        return plan

    def _execute_mark(self, plan: Plan, line: str) -> Plan:
        pattern = r"^mark:\s*(\d+)\s*=\s*(todo|done)\s*$"
        match = re.match(pattern, line, flags=re.IGNORECASE)
        if not match:
            return plan

        target_id = int(match.group(1))
        status = match.group(2).lower()

        step = self._find_step(plan, target_id)
        if step is not None:
            step.status = status
        return plan

    def _alloc_temp_id(self) -> int:
        temp_id = self._next_temp_id
        self._next_temp_id -= 1
        return temp_id

    @staticmethod
    def _find_index(plan: Plan, target_id: int) -> Optional[int]:
        for i, step in enumerate(plan):
            if step.id == target_id:
                return i
        return None

    @staticmethod
    def _find_step(plan: Plan, target_id: int) -> Optional[PlanStep]:
        for step in plan:
            if step.id == target_id:
                return step
        return None

    @staticmethod
    def _renumber(plan: Plan) -> Plan:
        for i, step in enumerate(plan, start=1):
            step.id = i
        return plan
