import json

FORMAT_REMINDER = """Your previous response could not be parsed. Respond with ONLY a JSON object in this exact form:
{ "primary_cause": "<short phrase>", "secondary_cause": "<short phrase or null>",
  "rationale": "<2-5 sentences>", "evidence": ["step N: <what it shows>", "..."] }"""

class RecordParser:
    """Parses a labeler/judge response into the structured record (protocol section 3)."""

    def parse(self, response: str) -> dict:
        # Extract the JSON object substring (models may wrap it in fences or prose)
        start = response.find("{")
        end = response.rfind("}")
        if start == -1 or end <= start:
            return None
        try:
            data = json.loads(response[start:end + 1])
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
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
