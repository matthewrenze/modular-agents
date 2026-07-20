from interp.diagnosis.record import RecordParser, ExtendedRecordParser

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

def extended_response(**overrides):
    data = {"primary_cause": "position-miscount-skip", "secondary_cause": "failed-move-desync",
            "root_cause_step": 12, "faulty_module": "planner", "confidence": 0.85,
            "corrective_action": "Execute go west at step 12.",
            "rationale": "The agent skipped instruction 12.", "evidence": ["step 12: skipped go west"]}
    data.update(overrides)
    import json
    return json.dumps(data)

class TestExtendedRecordParser:

    def test_parses_full_valid_record(self):
        record = ExtendedRecordParser().parse(extended_response())
        assert record == {"primary_cause": "position-miscount-skip",
                          "secondary_cause": "failed-move-desync",
                          "root_cause_step": 12, "faulty_module": "planner", "confidence": 0.85,
                          "corrective_action": "Execute go west at step 12.",
                          "rationale": "The agent skipped instruction 12.",
                          "evidence": ["step 12: skipped go west"]}

    def test_parses_json_in_code_fences(self):
        response = "```json\n" + extended_response() + "\n```"
        assert ExtendedRecordParser().parse(response)["primary_cause"] == "position-miscount-skip"

    def test_normalizes_primary_cause_case_and_backticks(self):
        record = ExtendedRecordParser().parse(extended_response(primary_cause="`Position-Miscount-Skip`"))
        assert record["primary_cause"] == "position-miscount-skip"

    def test_accepts_every_c2_taxonomy_slug(self):
        slugs = ["position-miscount-skip", "extra-move-insertion", "direction-misread",
                 "lost-place-reanchor", "route-copy-corruption", "checklist-overtick-skip",
                 "intent-action-mismatch", "cooking-recipe-errors", "capacity-misbelief-loop",
                 "failed-move-desync", "hallucinated-state-quit", "malformed-action-output",
                 "abandoned-prescribed-route", "other"]
        for slug in slugs:
            assert ExtendedRecordParser().parse(extended_response(primary_cause=slug))["primary_cause"] == slug

    def test_returns_none_when_primary_cause_not_in_taxonomy(self):
        assert ExtendedRecordParser().parse(extended_response(primary_cause="off-by-one navigation")) is None

    def test_returns_none_on_retired_c1_primary_slug(self):
        assert ExtendedRecordParser().parse(extended_response(primary_cause="route-transcription-errors")) is None

    def test_retired_c1_secondary_slug_becomes_null(self):
        record = ExtendedRecordParser().parse(extended_response(secondary_cause="lost-sequence-position"))
        assert record["secondary_cause"] is None

    def test_returns_none_when_primary_cause_missing(self):
        assert ExtendedRecordParser().parse('{"secondary_cause": "other"}') is None

    def test_accepts_other_as_primary_cause(self):
        assert ExtendedRecordParser().parse(extended_response(primary_cause="other"))["primary_cause"] == "other"

    def test_invalid_secondary_cause_becomes_null(self):
        record = ExtendedRecordParser().parse(extended_response(secondary_cause="not a slug"))
        assert record["secondary_cause"] is None

    def test_null_secondary_cause_stays_null(self):
        record = ExtendedRecordParser().parse(extended_response(secondary_cause=None))
        assert record["secondary_cause"] is None

    def test_root_cause_step_accepts_numeric_string(self):
        record = ExtendedRecordParser().parse(extended_response(root_cause_step="34"))
        assert record["root_cause_step"] == 34

    def test_root_cause_step_null_stays_null(self):
        assert ExtendedRecordParser().parse(extended_response(root_cause_step=None))["root_cause_step"] is None

    def test_root_cause_step_invalid_becomes_null(self):
        assert ExtendedRecordParser().parse(extended_response(root_cause_step="early on"))["root_cause_step"] is None

    def test_root_cause_step_boolean_becomes_null(self):
        assert ExtendedRecordParser().parse(extended_response(root_cause_step=True))["root_cause_step"] is None

    def test_root_cause_step_negative_becomes_null(self):
        assert ExtendedRecordParser().parse(extended_response(root_cause_step=-3))["root_cause_step"] is None

    def test_faulty_module_normalized(self):
        assert ExtendedRecordParser().parse(extended_response(faulty_module=" Planner "))["faulty_module"] == "planner"

    def test_faulty_module_invalid_becomes_null(self):
        assert ExtendedRecordParser().parse(extended_response(faulty_module="environment"))["faulty_module"] is None

    def test_faulty_module_null_stays_null(self):
        assert ExtendedRecordParser().parse(extended_response(faulty_module=None))["faulty_module"] is None

    def test_confidence_integer_becomes_float(self):
        record = ExtendedRecordParser().parse(extended_response(confidence=1))
        assert record["confidence"] == 1.0
        assert isinstance(record["confidence"], float)

    def test_confidence_out_of_range_becomes_null(self):
        assert ExtendedRecordParser().parse(extended_response(confidence=1.5))["confidence"] is None

    def test_confidence_non_numeric_becomes_null(self):
        assert ExtendedRecordParser().parse(extended_response(confidence="high"))["confidence"] is None

    def test_confidence_boolean_becomes_null(self):
        assert ExtendedRecordParser().parse(extended_response(confidence=True))["confidence"] is None

    def test_missing_extended_fields_get_defaults(self):
        record = ExtendedRecordParser().parse('{"primary_cause": "other"}')
        assert record == {"primary_cause": "other", "secondary_cause": None, "root_cause_step": None,
                          "faulty_module": None, "confidence": None, "corrective_action": "",
                          "rationale": "", "evidence": []}

    def test_returns_none_on_unparseable_text(self):
        assert ExtendedRecordParser().parse("The route drifted.") is None
