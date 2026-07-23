import json

class SolutionReader:

    def read(self, split_name: str, eval_name: str, episode_id: int) -> list:
        # Resolve the episode's jsonl row (episode-N = row N-1) and split the solution commands
        base_name = eval_name.split("-")[0] + "-" + eval_name.split("-")[1]
        jsonl_path = f"../data/evals/{split_name}/{base_name}/{eval_name}.jsonl"
        with open(jsonl_path, "r", encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        solution = rows[episode_id - 1]["solution"]
        return [command.strip() for command in solution.split(",") if command.strip()]
