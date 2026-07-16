from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple

@dataclass
class GameTruth:
    rooms: Set[str] = field(default_factory=set)
    links: Dict[Tuple[str, str], str] = field(default_factory=dict)                # (room, direction) -> room
    objects: Set[str] = field(default_factory=set)
    placements: Dict[str, Tuple[str, Optional[str]]] = field(default_factory=dict)  # object -> (room, container)
    doors: Dict[str, Set[str]] = field(default_factory=dict)                        # door -> its two adjacent rooms
