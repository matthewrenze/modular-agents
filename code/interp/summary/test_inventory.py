from interp.summary.inventory import parse_inventory

class TestParseInventory:

    def test_parses_an_empty_inventory(self):
        assert parse_inventory("You are carrying nothing.") == set()

    def test_parses_a_single_item(self):
        assert parse_inventory("You are carrying: an old key.") == {"old key"}

    def test_parses_a_comma_and_conjunction_list(self):
        text = "You are carrying: a knife, a white onion and a yellow apple."
        assert parse_inventory(text) == {"knife", "white onion", "yellow apple"}

    def test_drops_state_adjectives_so_cooking_is_not_an_inventory_change(self):
        before = parse_inventory("You are carrying: a raw yellow potato.")
        after = parse_inventory("You are carrying: a sliced raw yellow potato.")
        assert before == after == {"yellow potato"}

    def test_parses_an_empty_string(self):
        assert parse_inventory("") == set()
