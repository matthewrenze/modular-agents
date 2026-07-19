import json

TAXONOMY = ["lost-sequence-position", "route-transcription-errors", "cooking-recipe-errors",
            "capacity-misbelief-loop", "failed-move-desync", "hallucinated-state-quit",
            "malformed-action-output", "abandoned-prescribed-route", "other"]

MODULES = ["summarizer", "memorizer", "planner", "reasoner", "actor"]

FORMAT_REMINDER = """Your previous response could not be parsed. Respond with ONLY a JSON object in this exact form:
{ "primary_cause": "<short phrase>", "secondary_cause": "<short phrase or null>",
  "rationale": "<2-5 sentences>", "evidence": ["step N: <what it shows>", "..."] }"""

FORMAT_REMINDER_EXTENDED = """Your previous response could not be parsed. Respond with ONLY a JSON object in this exact form, with "primary_cause" chosen from the fixed taxonomy slugs listed in the instructions:
{ "primary_cause": "<slug>", "secondary_cause": "<slug or null>",
  "root_cause_step": <integer or null>, "faulty_module": "<module or null>",
  "confidence": <0.0-1.0>, "corrective_action": "<one line>",
  "rationale": "<2-5 sentences>", "evidence": ["step N: <what it shows>", "..."] }"""

def extract_json(response: str) -> dict:
    # Extract the JSON object substring (models may wrap it in fences or prose)
    start = response.find("{")
    end = response.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(response[start:end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None

class RecordParser:
    """Parses a labeler/judge response into the structured record (protocol section 3)."""

    def parse(self, response: str) -> dict:
        data = extract_json(response)
        if data is None:
            return None

        # The scored field must be a non-empty string; the rest get lenient defaults
        primary_cause = data.get("primary_cause")
        if not isinstance(primary_cause, str) or not primary_cause.strip():
            return None
        secondary_cause = data.get("secondary_cause")
        if not isinstance(secondary_cause, str) or not secondary_cause.strip():
            secondary_cause = None
        rationale = data.get("rationale") if isinstance(data.get("rationale"), str) else ""
        evidence = data.get("evidence") if isinstance(data.get("evidence"), list) else []
        return {"primary_cause": primary_cause.strip(), "secondary_cause": secondary_cause,
                "rationale": rationale, "evidence": [str(item) for item in evidence]}

class ExtendedRecordParser:
    """Parses the extended 8-field record for Phases C/D (protocol section 3, Gate 2 schema)."""

    def parse(self, response: str) -> dict:
        data = extract_json(response)
        if data is None:
            return None

        # The scored field must be a valid taxonomy slug; the rest get lenient defaults
        primary_cause = self._parse_slug(data.get("primary_cause"), TAXONOMY)
        if primary_cause is None:
            return None
        rationale = data.get("rationale") if isinstance(data.get("rationale"), str) else ""
        evidence = data.get("evidence") if isinstance(data.get("evidence"), list) else []
        corrective_action = data.get("corrective_action")
        corrective_action = corrective_action.strip() if isinstance(corrective_action, str) else ""
        return {"primary_cause": primary_cause,
                "secondary_cause": self._parse_slug(data.get("secondary_cause"), TAXONOMY),
                "root_cause_step": self._parse_step(data.get("root_cause_step")),
                "faulty_module": self._parse_slug(data.get("faulty_module"), MODULES),
                "confidence": self._parse_confidence(data.get("confidence")),
                "corrective_action": corrective_action,
                "rationale": rationale, "evidence": [str(item) for item in evidence]}

    def _parse_slug(self, value, allowed: list) -> str:
        if not isinstance(value, str):
            return None
        slug = value.strip().strip("`").lower()
        return slug if slug in allowed else None

    def _parse_step(self, value) -> int:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value if value >= 0 else None
        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())
        return None

    def _parse_confidence(self, value) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return float(value) if 0.0 <= value <= 1.0 else None
