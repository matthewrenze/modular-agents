import re
from typing import Optional, Tuple
from interp.memory.memory_facts import MemoryFacts

DIRECTIONS = {"north", "south", "east", "west"}
UNKNOWNS = {"?", "??", "none", "unknown", "unexplored", "unvisited", "tbd", "n/a",
            "blocked", "no exit", "nowhere", "wall", "unavailable", "dead end", "nothing", "∅", "✗", "x"}
OP_KEYS = {"update", "create", "delete", "add", "remove", "new"}
INVENTORY_NAMES = {"inventory", "player", "me", "carried", "held", "in inventory", "on person", "with us"}

def clean_name(name: str) -> str:
    # Strip bullet/numbering/quote prefixes and surrounding quotes ('- bedroom', '"study"')
    name = re.sub(r"^[\s\-\*\.\)\"']+|^\d+[\.\)]\s*", "", name.strip())
    return name.strip("\"' ").strip()

class MemoryFactParser:

    def parse(self, memories: dict) -> MemoryFacts:
        facts = MemoryFacts()
        for key, value in memories.items():
            self.parse_memory(str(key), str(value), facts)
        return facts

    def parse_memory(self, key: str, value: str, facts: MemoryFacts, recovered: bool = False):
        key = clean_name(key.lower())
        value = value.strip().lower()

        # Recover the real memory from an op-prefixed line ('Update: "study: rooms = ..."')
        if not recovered and key in OP_KEYS and ":" in value:
            inner_key, inner_value = value.strip("\"' ").split(":", 1)
            self.parse_memory(inner_key, inner_value, facts, recovered=True)
            return
        matched = False

        # Extract room links from a "rooms = {dir = dest, ...}" block
        rooms_block = re.search(r"rooms\s*=\s*\{([^{}]*)\}", value)
        if rooms_block:
            matched = True
            for pair in rooms_block.group(1).split(","):
                if "=" not in pair:
                    continue
                direction, destination = (part.strip() for part in pair.split("=", 1))
                destination = clean_name(destination)
                if direction not in DIRECTIONS:
                    continue
                if destination in UNKNOWNS:
                    facts.unknown_links += 1
                else:
                    facts.room_links.append((key, direction, destination))

        # Extract an object location from a "location = ..." value
        location = re.search(r"location\s*=\s*(\{[^{}]*\}|[^,{}]+)", value)
        if location:
            room, container = self.parse_location(location.group(1))
            if room:
                matched = True
                facts.object_locations.append((key, room, container))

        if not matched:
            facts.residue.append((key, value))

    def parse_location(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        text = text.strip()

        # Structured form: "location = {room = bedroom, in = drawer}"; plain form: "location = kitchen"
        if text.startswith("{"):
            properties = {}
            for pair in text.strip("{}").split(","):
                if "=" not in pair:
                    continue
                name, value = (part.strip() for part in pair.split("=", 1))
                properties[name] = value
            room = properties.get("room")
            container = properties.get("in") or properties.get("on")
            if container == "floor":
                container = None
        else:
            room, container = text, None

        if room is None:
            return None, None
        room = clean_name(room)
        if room in UNKNOWNS:
            return None, None
        if room in INVENTORY_NAMES:
            room = "inventory"
        return room, container and clean_name(container)
