from interp.diagnosis.record import RecordParser

class TestRecordParser:

    def test_parses_plain_json(self):
        response = ('{"primary_cause": "false belief about exits", "secondary_cause": null,'
                    ' "rationale": "The agent believed a wall was a door.", "evidence": ["step 12: wrong exit"]}')
        record = RecordParser().parse(response)
        assert record == {"primary_cause": "false belief about exits", "secondary_cause": None,
                          "rationale": "The agent believed a wall was a door.",
                          "evidence": ["step 12: wrong exit"]}

    def test_parses_json_in_code_fences(self):
        response = '```json\n{"primary_cause": "give up", "secondary_cause": null, "rationale": "r", "evidence": []}\n```'
        assert RecordParser().parse(response)["primary_cause"] == "give up"

    def test_parses_json_wrapped_in_prose(self):
        response = 'Here is my diagnosis:\n{"primary_cause": "desync", "secondary_cause": "memory junk", "rationale": "r", "evidence": []}\nHope this helps.'
        record = RecordParser().parse(response)
        assert record["primary_cause"] == "desync"
        assert record["secondary_cause"] == "memory junk"

    def test_defaults_missing_optional_fields(self):
        record = RecordParser().parse('{"primary_cause": "desync"}')
        assert record == {"primary_cause": "desync", "secondary_cause": None, "rationale": "", "evidence": []}

    def test_returns_none_when_primary_cause_missing(self):
        assert RecordParser().parse('{"secondary_cause": "desync", "rationale": "r", "evidence": []}') is None

    def test_returns_none_when_primary_cause_empty(self):
        assert RecordParser().parse('{"primary_cause": "  "}') is None

    def test_returns_none_on_unparseable_text(self):
        assert RecordParser().parse("The failure was caused by a false belief.") is None

    def test_returns_none_on_non_object_json(self):
        assert RecordParser().parse('["desync"]') is None
