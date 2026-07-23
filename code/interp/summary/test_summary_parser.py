from interp.summary.summary_parser import SummaryParser

def parse(text):
    return SummaryParser().parse(text)

class TestParse:

    def test_parses_the_start_summary(self):
        claims = parse("start → location = bedroom")
        assert claims.parseable
        assert claims.echo == "start"
        assert claims.locations == ["bedroom"]

    def test_parses_each_clause_type(self):
        claims = parse("take old key from antique trunk → inventory += old key; score += 1")
        assert claims.echo == "take old key from antique trunk"
        assert claims.inv_added == ["old key"]
        assert claims.score_deltas == [1]

    def test_parses_inventory_removal_failure_and_object_state(self):
        claims = parse("slice apple → inventory -= apple; failure = none; carrot = diced")
        assert claims.inv_removed == ["apple"]
        assert claims.failures == ["none"]
        assert claims.obj_states == [("carrot", "diced")]

    def test_unclassifiable_clauses_land_in_others(self):
        claims = parse("look → no coin visible; score -= 1")
        assert claims.others == ["no coin visible", "score -= 1"]

    def test_empty_clauses_are_ignored(self):
        claims = parse("go east → location = kitchen; ")
        assert claims.locations == ["kitchen"]
        assert claims.others == []

    def test_supports_the_ascii_arrow(self):
        claims = parse("go east -> location = kitchen")
        assert claims.locations == ["kitchen"]

    def test_narration_without_an_arrow_is_unparseable(self):
        claims = parse("Let me analyze what happened at step 91.")
        assert not claims.parseable
        assert claims.locations == []

    def test_multiline_takes_the_last_arrow_line(self):
        text = ("open fridge → fridge = open; inventory -= cookbook\n"
                "Wait, I need to follow the rules.\n"
                "open fridge → fridge = open")
        claims = parse(text)
        assert claims.multiline
        assert claims.obj_states == [("fridge", "open")]
        assert claims.inv_removed == []

    def test_score_clause_tolerates_trailing_text(self):
        claims = parse("go east → score += 2 (total 3)")
        assert claims.score_deltas == [2]

    def test_clause_matching_is_case_insensitive(self):
        claims = parse("go east → Location = Kitchen; Inventory += Knife")
        assert claims.locations == ["Kitchen"]
        assert claims.inv_added == ["Knife"]
