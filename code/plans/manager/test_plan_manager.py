from plans.manager.plan_manager import PlanManager
from plans.plan_step import PlanStep

class TestPlanManager:

    def test_execute(self):
        manager = PlanManager()
        plan = [
            PlanStep(id=1, status="todo", label="step 1"),
            PlanStep(id=2, status="todo", label="step 2"),
            PlanStep(id=3, status="todo", label="step 3"),
            PlanStep(id=4, status="todo", label="step 4"),
        ]

        operations = """
        add: step 5
        insert: 2 = step 6
        mark: 1 = done        
        delete: 3
        update: 4 = step 4.1
        """

        updated_plan = manager.execute(plan, operations)

        assert len(updated_plan) == 5
        assert_plan_step(updated_plan[0], id=1, status="done", label="step 1")
        assert_plan_step(updated_plan[1], id=2, status="todo", label="step 6")
        assert_plan_step(updated_plan[2], id=3, status="todo", label="step 2")
        assert_plan_step(updated_plan[3], id=4, status="todo", label="step 4.1")
        assert_plan_step(updated_plan[4], id=5, status="todo", label="step 5")

    def test_insert_with_equal_ids(self):
        manager = PlanManager()
        plan = [
            PlanStep(id=1, status="todo", label="step 1"),
            PlanStep(id=2, status="todo", label="step 2"),
        ]

        operations = """
        insert: 2 = step 1.1
        insert: 2 = step 1.2
        """

        updated_plan = manager.execute(plan, operations)

        assert len(updated_plan) == 4
        assert_plan_step(updated_plan[0], id=1, status="todo", label="step 1")
        assert_plan_step(updated_plan[1], id=2, status="todo", label="step 1.1")
        assert_plan_step(updated_plan[2], id=3, status="todo", label="step 1.2")
        assert_plan_step(updated_plan[3], id=4, status="todo", label="step 2")

def assert_plan_step(step: PlanStep, id: int, status: str, label: str):
    assert step.id == id
    assert step.status == status
    assert step.label == label

