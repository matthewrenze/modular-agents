import re
from interp.summary.summary_claims import SummaryClaims

ARROWS = ("→", "->")
LOCATION_PATTERN = re.compile(r"^location\s*=\s*(.+)$", re.I)
INVENTORY_PATTERN = re.compile(r"^inventory\s*(\+=|-=)\s*(.+)$", re.I)
SCORE_PATTERN = re.compile(r"^score\s*\+=\s*(\d+)\b", re.I)
FAILURE_PATTERN = re.compile(r"^failure\s*=\s*(.+)$", re.I)
OBJECT_PATTERN = re.compile(r"^([^=]+?)\s*=\s*(.+)$")

class SummaryParser:

    def parse(self, text: str) -> SummaryClaims:
        lines = str(text).strip().splitlines()
        multiline = len(lines) > 1

        # The summary is the last arrow-bearing line (multiline dumps end with the self-corrected answer)
        line = next((line for line in reversed(lines) if any(arrow in line for arrow in ARROWS)), None)
        if line is None:
            return SummaryClaims(parseable=False, multiline=multiline)

        arrow = next(arrow for arrow in ARROWS if arrow in line)
        echo, outcome = line.split(arrow, 1)
        claims = SummaryClaims(multiline=multiline, echo=echo.strip())
        for clause in outcome.split(";"):
            self.parse_clause(clause.strip(), claims)
        return claims

    def parse_clause(self, clause: str, claims: SummaryClaims):
        if not clause:
            return
        if match := LOCATION_PATTERN.match(clause):
            claims.locations.append(match.group(1).strip())
        elif match := INVENTORY_PATTERN.match(clause):
            items = claims.inv_added if match.group(1) == "+=" else claims.inv_removed
            items.append(match.group(2).strip())
        elif match := SCORE_PATTERN.match(clause):
            claims.score_deltas.append(int(match.group(1)))
        elif match := FAILURE_PATTERN.match(clause):
            claims.failures.append(match.group(1).strip())
        elif (match := OBJECT_PATTERN.match(clause)) and not clause.lower().startswith("score"):
            claims.obj_states.append((match.group(1).strip(), match.group(2).strip()))
        else:
            claims.others.append(clause)
