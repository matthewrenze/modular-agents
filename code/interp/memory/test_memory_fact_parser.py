from interp.memory.memory_fact_parser import MemoryFactParser

class TestMemoryFactParser:

    def test_room_links(self):
        memories = {"dish-pit": "rooms = {north = steam room}",
                    "steam room": "rooms = {north = closet, south = dish-pit}"}
        facts = MemoryFactParser().parse(memories)
        assert facts.room_links == [("dish-pit", "north", "steam room"),
                                    ("steam room", "north", "closet"),
                                    ("steam room", "south", "dish-pit")]
        assert facts.unknown_links == 0
        assert facts.residue == []

    def test_unknown_links_are_counted_not_scored(self):
        memories = {"bedroom": "rooms = {north = living room, east = ?, south = none}"}
        facts = MemoryFactParser().parse(memories)
        assert facts.room_links == [("bedroom", "north", "living room")]
        assert facts.unknown_links == 2

    def test_room_memory_with_doors_block_keeps_links(self):
        memories = {"bedroom": "rooms = {north = living room}, doors = {east = wooden door}"}
        facts = MemoryFactParser().parse(memories)
        assert facts.room_links == [("bedroom", "north", "living room")]
        assert facts.residue == []

    def test_non_cardinal_directions_are_skipped(self):
        memories = {"study": "rooms = {east = closet, up = attic}"}
        facts = MemoryFactParser().parse(memories)
        assert facts.room_links == [("study", "east", "closet")]

    def test_object_location_with_room_and_container(self):
        memories = {"gold key": "location = {room = bedroom, in = drawer}"}
        facts = MemoryFactParser().parse(memories)
        assert facts.object_locations == [("gold key", "bedroom", "drawer")]

    def test_object_location_on_floor_has_no_container(self):
        memories = {"coin": "location = {room = kitchen, on = floor}"}
        facts = MemoryFactParser().parse(memories)
        assert facts.object_locations == [("coin", "kitchen", None)]

    def test_object_location_plain_room(self):
        memories = {"screen door": "location = kitchen, direction = east, state = {closed, locked}"}
        facts = MemoryFactParser().parse(memories)
        assert facts.object_locations == [("screen door", "kitchen", None)]

    def test_unscoreable_memories_land_in_residue(self):
        memories = {"safe": "code = 1234",
                    "rule 2": "To cut an object, it must first be in my inventory",
                    "recipe 1": "ingredients = {bread, jelly}, steps = {1. spread jelly}",
                    "error": "Invalid memory update operation: 'blah'"}
        facts = MemoryFactParser().parse(memories)
        assert facts.room_links == []
        assert facts.object_locations == []
        assert [key for key, value in facts.residue] == ["safe", "rule 2", "recipe 1", "error"]

    def test_no_exit_claims_count_as_unknown(self):
        memories = {"study": "rooms = {north = blocked, south = nowhere, east = wall, west = closet}"}
        facts = MemoryFactParser().parse(memories)
        assert facts.room_links == [("study", "west", "closet")]
        assert facts.unknown_links == 3

    def test_bullet_and_quote_prefixes_are_cleaned(self):
        memories = {"- Bedroom": 'rooms = {north = - kitchen, east = "study"}'}
        facts = MemoryFactParser().parse(memories)
        assert facts.room_links == [("bedroom", "north", "kitchen"), ("bedroom", "east", "study")]

    def test_op_keyed_memories_are_recovered(self):
        memories = {"Update": '"Serious Study: rooms = {east = Cozy Bedroom}"',
                    "Create": "'gold key: location = {room = bedroom, in = drawer}'"}
        facts = MemoryFactParser().parse(memories)
        assert facts.room_links == [("serious study", "east", "cozy bedroom")]
        assert facts.object_locations == [("gold key", "bedroom", "drawer")]
        assert facts.residue == []

    def test_op_keyed_memory_without_content_is_residue(self):
        memories = {"Update": "the map is now complete"}
        facts = MemoryFactParser().parse(memories)
        assert facts.residue == [("update", "the map is now complete")]

    def test_inventory_locations_are_normalized(self):
        memories = {"coin": "location = player", "gold key": "location = {room = inventory}"}
        facts = MemoryFactParser().parse(memories)
        assert facts.object_locations == [("coin", "inventory", None), ("gold key", "inventory", None)]

    def test_keys_and_values_are_lowercased(self):
        memories = {"Steam Room": "rooms = {North = Closet}",
                    "Gold Key": "location = {room = Bedroom, in = Drawer}"}
        facts = MemoryFactParser().parse(memories)
        assert facts.room_links == [("steam room", "north", "closet")]
        assert facts.object_locations == [("gold key", "bedroom", "drawer")]
