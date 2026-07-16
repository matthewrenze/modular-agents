from interp.plan.plan_parser import PlanParser

PLAN = """- [x] Get the old key
  - [x] Open the antique trunk
  - [x] Take the old key from the antique trunk
- [ ] Open the wooden door
  - [x] Unlock the wooden door with the old key
  - [ ] Open the wooden door
- [ ] Go east
"""

class TestPlanParser:

    def test_parses_items_with_depth_and_checked(self):
        plan = PlanParser().parse(PLAN)
        assert len(plan.items) == 7
        assert (plan.items[0].depth, plan.items[0].checked, plan.items[0].text) == (0, True, "Get the old key")
        assert (plan.items[1].depth, plan.items[1].checked) == (1, True)
        assert plan.items[5].text == "Open the wooden door"

    def test_leaves_are_items_without_children(self):
        plan = PlanParser().parse(PLAN)
        assert [item.text for item in plan.leaves()] == [
            "Open the antique trunk", "Take the old key from the antique trunk",
            "Unlock the wooden door with the old key", "Open the wooden door", "Go east"]

    def test_current_open_leaf_is_first_unchecked_leaf(self):
        plan = PlanParser().parse(PLAN)
        assert plan.current_open_leaf().text == "Open the wooden door"

    def test_open_leaves_lists_all_unchecked_leaves(self):
        plan = PlanParser().parse(PLAN)
        assert [item.text for item in plan.open_leaves()] == ["Open the wooden door", "Go east"]

    def test_fully_checked_plan_has_no_open_leaf(self):
        plan = PlanParser().parse("- [x] Go east\n- [X] Go west\n")
        assert plan.current_open_leaf() is None

    def test_invalid_lines_are_counted_not_parsed(self):
        plan = PlanParser().parse("- [x] Go east\nsome stray text\n\n- [ ] Go west\n")
        assert len(plan.items) == 2
        assert plan.invalid_lines == 1

    def test_empty_plan(self):
        plan = PlanParser().parse("")
        assert plan.items == []
        assert plan.current_open_leaf() is None
