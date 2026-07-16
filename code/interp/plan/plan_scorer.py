from interp.plan.action_matcher import ActionMatcher, normalize
from interp.plan.plan_parser import PlanParser

class PlanScorer:
    def __init__(self, parser: PlanParser, matcher: ActionMatcher):
        self.parser = parser
        self.matcher = matcher

    def score_agreement(self, steps: list) -> dict:
        # Match each executed action against the plan's current open leaf at that step
        scores = {"n_steps": 0, "n_current_exact": 0, "n_current_fuzzy": 0, "n_any_open": 0,
                  "n_mismatch": 0, "n_no_open": 0, "n_no_plan": 0, "n_unparseable": 0, "mismatches": []}
        parsed = {}
        for plan_text, action in steps:
            scores["n_steps"] += 1
            if not plan_text.strip():
                scores["n_no_plan"] += 1
                continue
            if plan_text not in parsed:
                parsed[plan_text] = self.parser.parse(plan_text)
            if not parsed[plan_text].leaves():
                scores["n_unparseable"] += 1
                continue
            open_leaves = parsed[plan_text].open_leaves()
            if not open_leaves:
                scores["n_no_open"] += 1
                continue
            match = self.matcher.match(action, open_leaves[0].text)
            if match:
                scores[f"n_current_{match}"] += 1
            elif any(self.matcher.match(action, leaf.text) for leaf in open_leaves[1:]):
                scores["n_any_open"] += 1
            else:
                scores["n_mismatch"] += 1
                scores["mismatches"].append((action, open_leaves[0].text))
        return scores

    def score_correctness(self, plan_text: str, solution: list) -> dict:
        # Longest common subsequence between the plan's leaves and the solution commands
        leaves = [item.text for item in self.parser.parse(plan_text).leaves()]
        table = [[0] * (len(solution) + 1) for _ in range(len(leaves) + 1)]
        for i, leaf in enumerate(leaves):
            for j, command in enumerate(solution):
                if self.matcher.match(command, leaf):
                    table[i + 1][j + 1] = table[i][j] + 1
                else:
                    table[i + 1][j + 1] = max(table[i][j + 1], table[i + 1][j])
        return {"lcs": table[-1][-1], "n_leaves": len(leaves), "n_solution": len(solution)}

    def score_hygiene(self, plan_text: str) -> dict:
        # Parse validity and repetition pathologies on a plan snapshot
        plan = self.parser.parse(plan_text)
        leaves = [normalize(item.text) for item in plan.leaves()]
        max_run, run = 0, 0
        for previous, current in zip([None] + leaves, leaves):
            run = run + 1 if current == previous else 1
            max_run = max(max_run, run)
        return {"n_lines": plan.n_lines, "n_invalid_lines": plan.invalid_lines,
                "n_leaves": len(leaves), "n_duplicate_leaves": len(leaves) - len(set(leaves)),
                "max_leaf_run": max_run}
