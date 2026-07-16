import re
from interp.plan.plan import Plan, PlanItem

ITEM_PATTERN = re.compile(r"^(\s*)[-*] \[( |x|X)\] (.+?)\s*$")

class PlanParser:

    def parse(self, text: str) -> Plan:
        plan = Plan()
        for line in text.splitlines():
            if not line.strip():
                continue
            plan.n_lines += 1
            match = ITEM_PATTERN.match(line)
            if not match:
                plan.invalid_lines += 1
                continue
            depth = len(match.group(1)) // 2
            plan.items.append(PlanItem(depth=depth, checked=match.group(2) != " ", text=match.group(3)))

        # An item is a parent (not a leaf) if the next item is indented deeper
        for item, next_item in zip(plan.items, plan.items[1:]):
            item.is_leaf = next_item.depth <= item.depth
        return plan
