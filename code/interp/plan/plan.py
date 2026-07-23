from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class PlanItem:
    depth: int
    checked: bool
    text: str
    is_leaf: bool = True

@dataclass
class Plan:
    items: List[PlanItem] = field(default_factory=list)
    invalid_lines: int = 0
    n_lines: int = 0

    def leaves(self) -> List[PlanItem]:
        return [item for item in self.items if item.is_leaf]

    def open_leaves(self) -> List[PlanItem]:
        return [item for item in self.leaves() if not item.checked]

    def current_open_leaf(self) -> Optional[PlanItem]:
        open_leaves = self.open_leaves()
        return open_leaves[0] if open_leaves else None
