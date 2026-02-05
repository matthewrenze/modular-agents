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

        assert updated_plan[0].id == 1
        assert updated_plan[0].status == "done"
        assert updated_plan[0].label == "step 1"

        assert updated_plan[1].id == 2
        assert updated_plan[1].status == "todo"
        assert updated_plan[1].label == "step 6"

        assert updated_plan[2].id == 3
        assert updated_plan[2].status == "todo"
        assert updated_plan[2].label == "step 2"

        assert updated_plan[3].id == 4
        assert updated_plan[3].status == "todo"
        assert updated_plan[3].label == "step 4.1"

        assert updated_plan[4].id == 5
        assert updated_plan[4].status == "todo"
        assert updated_plan[4].label == "step 5"
