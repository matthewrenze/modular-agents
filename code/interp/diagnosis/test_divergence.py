from interp.diagnosis.divergence import first_divergence, corrective_matches

class TestFirstDivergence:

    def test_divergence_step_and_expected_command(self):
        assert first_divergence(["go east", "go north"], ["go east", "go east"]) == (2, "go east")

    def test_prefix_has_no_divergence(self):
        assert first_divergence(["go east"], ["go east", "go north"]) is None

    def test_normalization(self):
        assert first_divergence(["Go  EAST", "go north"], ["go east", "go north"]) is None

    def test_extra_actions_beyond_solution_ignored(self):
        assert first_divergence(["go east", "go north"], ["go east"]) is None

class TestCorrectiveMatches:

    def test_command_named_in_text(self):
        assert corrective_matches("execute instruction 41 ('go east')", "go east")

    def test_whitespace_and_case(self):
        assert corrective_matches("Action: Go   EAST", "go east")

    def test_wrong_command(self):
        assert not corrective_matches("go west instead", "go east")

    def test_null_text(self):
        assert not corrective_matches(None, "go east")
