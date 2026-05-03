import pandas as pd
from params.parameters import Parameters

class EvalFactory:

    @staticmethod
    def create(params: Parameters):
        if params.eval_name.startswith("tw-"):
            base_name = params.eval_name.split("-")[0] + "-" + params.eval_name.split("-")[1]
            file_path = f"../data/evals/{params.split_name}/{base_name}/{params.eval_name}.jsonl"
            eval = pd.read_json(file_path, lines=True)
            return eval
        else:
            raise ValueError(f"Unknown eval name: {params.eval_name}")

