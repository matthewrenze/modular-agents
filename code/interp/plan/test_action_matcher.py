from interp.plan.action_matcher import ActionMatcher, normalize

class TestNormalize:

    def test_lowercases_and_strips_articles_prepositions_and_punctuation(self):
        assert normalize("Take the old key from the antique trunk.") == "take old key antique trunk"

    def test_collapses_whitespace(self):
        assert normalize("go   east ") == "go east"

class TestNormalizeGameSynonyms:

    def test_movement_verbs_map_to_go(self):
        assert normalize("move north") == normalize("go north")
        assert normalize("Explore east from Kitchen") == normalize("go east kitchen")

    def test_cooking_verbs_map_to_cook(self):
        assert normalize("Grill the carrot with the BBQ") == normalize("cook carrot with bbq")

    def test_state_adjectives_are_dropped(self):
        assert normalize("take diced fried carrot") == normalize("take the fried carrot")

    def test_prepositions_are_dropped(self):
        assert normalize("Fry the white tuna on the stove") == normalize("cook white tuna with stove")

    def test_command_synonyms_map_to_the_executable_verb(self):
        assert normalize("insert the potato into the oven") == normalize("put potato in oven")
        assert normalize("read the cookbook") == normalize("examine cookbook")
        assert normalize("go back east") == normalize("go east")

    def test_prep_verbs_stay_distinct(self):
        assert normalize("slice the carrot") != normalize("chop the carrot")

    def test_appliances_stay_distinct(self):
        assert normalize("cook carrot with oven") != normalize("cook carrot with stove")

class TestActionMatcher:

    def test_exact_match_after_normalization(self):
        assert ActionMatcher().match("open the wooden door", "Open the wooden door") == "exact"

    def test_action_contained_in_item_is_fuzzy(self):
        assert ActionMatcher().match("go east", "Go east to the garden") == "fuzzy"

    def test_item_contained_in_action_is_fuzzy(self):
        assert ActionMatcher().match("take the apple from the refrigerator", "Take the apple") == "fuzzy"

    def test_containment_is_token_aligned(self):
        assert ActionMatcher().match("go east", "Forego eastern route") is None

    def test_no_match_returns_none(self):
        assert ActionMatcher().match("go west", "Open the wooden door") is None

    def test_empty_action_never_matches(self):
        assert ActionMatcher().match("", "Open the wooden door") is None
