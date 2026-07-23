from dataclasses import dataclass, field
from typing import List, Optional, Tuple

@dataclass
class MemoryFacts:
    room_links: List[Tuple[str, str, str]] = field(default_factory=list)          # (room, direction, destination)
    object_locations: List[Tuple[str, str, Optional[str]]] = field(default_factory=list)  # (object, room, container)
    unknown_links: int = 0                                                         # explicit unknowns ("?", "none")
    residue: List[Tuple[str, str]] = field(default_factory=list)                   # unscoreable memories (key, value)
