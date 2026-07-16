from interp.plan.action_matcher import ActionMatcher, normalize
from interp.summary.inventory import parse_inventory
from interp.summary.summary_claims import SummaryClaims
from interp.summary.summary_parser import SummaryParser

class SummaryScorer:
    def __init__(self, parser: SummaryParser, matcher: ActionMatcher):
        self.parser = parser
        self.matcher = matcher

    def score(self, steps: list) -> dict:
        # steps: (summary_text, env_diff) pairs from details.csv / EpisodeExtract.env_diffs()
        scores = {"n_steps": 0, "n_unparseable": 0, "n_multiline": 0,
                  "echo_exact": 0, "echo_fuzzy": 0, "echo_mismatch": 0,
                  "loc_tp": 0, "loc_fp": 0, "loc_redundant": 0, "loc_changes": 0, "loc_hits": 0,
                  "inv_tp": 0, "inv_fp": 0, "inv_changes": 0, "inv_hits": 0,
                  "inv_meal_changes": 0, "inv_meal_hits": 0,
                  "score_tp": 0, "score_fp": 0, "score_changes": 0, "score_hits": 0,
                  "n_obj_state": 0, "n_failure": 0, "n_other": 0,
                  "fp_claims": [], "missed_changes": [], "echo_mismatches": []}
        for summary, diff in steps:
            scores["n_steps"] += 1
            claims = self.parser.parse(summary)
            scores["n_unparseable"] += not claims.parseable
            scores["n_multiline"] += claims.multiline
            self.score_echo(claims, diff, scores)
            self.score_location(claims, diff, scores)
            if diff["prev_action"]:  # the start step has no prior state to diff against
                self.score_inventory(claims, diff, scores)
                self.score_score(claims, diff, scores)
            scores["n_obj_state"] += len(claims.obj_states)
            scores["n_failure"] += len(claims.failures)
            scores["n_other"] += len(claims.others)
        return scores

    def score_echo(self, claims: SummaryClaims, diff: dict, scores: dict):
        if not claims.parseable:
            return
        expected = str(diff["prev_action"]).strip() or "start"
        match = self.matcher.match(expected, claims.echo)
        if match:
            scores[f"echo_{match}"] += 1
        else:
            scores["echo_mismatch"] += 1
            scores["echo_mismatches"].append((claims.echo, expected))

    def score_location(self, claims: SummaryClaims, diff: dict, scores: dict):
        changed = diff["location_to"] != diff["location_from"]
        scores["loc_changes"] += changed
        hit = False
        for claimed in claims.locations:
            if self.matcher.match(claimed, diff["location_to"]):
                scores["loc_tp"] += 1
                scores["loc_redundant"] += not changed
                hit = True
            else:
                scores["loc_fp"] += 1
                scores["fp_claims"].append(("location", claimed, diff["location_to"]))
        if changed:
            scores["loc_hits"] += hit
            if not hit:
                scores["missed_changes"].append(("location", diff["location_to"]))

    def score_inventory(self, claims: SummaryClaims, diff: dict, scores: dict):
        before, after = parse_inventory(diff["inventory_from"]), parse_inventory(diff["inventory_to"])
        changes = {"added": after - before, "removed": before - after}
        n_changes = sum(len(items) for items in changes.values())
        scores["inv_changes"] += n_changes

        # Meal preparation consumes every ingredient at once, exceeding the summary's 3-outcome cap
        meal_step = normalize(str(diff["prev_action"])) == "prepare meal"
        scores["inv_meal_changes"] += n_changes if meal_step else 0
        hits = set()
        claimed_items = ([("added", item) for item in claims.inv_added] +
                         [("removed", item) for item in claims.inv_removed])
        for direction, claimed in claimed_items:
            match = next((item for item in changes[direction] if self.matcher.match(claimed, item)), None)
            if match:
                scores["inv_tp"] += 1
                hits.add((direction, match))
            else:
                scores["inv_fp"] += 1
                scores["fp_claims"].append((f"inventory_{direction}", claimed,
                                            " | ".join(sorted(changes[direction]))))
        scores["inv_hits"] += len(hits)
        scores["inv_meal_hits"] += len(hits) if meal_step else 0
        for direction, items in changes.items():
            for item in items:
                if (direction, item) not in hits:
                    scores["missed_changes"].append((f"inventory_{direction}", item))

    def score_score(self, claims: SummaryClaims, diff: dict, scores: dict):
        actual = int(diff["score_to"]) - int(diff["score_from"])
        scores["score_changes"] += actual != 0
        hit = False
        for claimed in claims.score_deltas:
            if claimed == actual:
                scores["score_tp"] += 1
                hit = True
            else:
                scores["score_fp"] += 1
                scores["fp_claims"].append(("score", str(claimed), str(actual)))
        if actual != 0:
            scores["score_hits"] += hit
            if not hit:
                scores["missed_changes"].append(("score", str(actual)))
