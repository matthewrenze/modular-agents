# Import packages
import sys
import argparse
from episodes.episode import Episode


def build_parser():
    parser = argparse.ArgumentParser(description="Run a single eval episode.")
    parser.add_argument("--split", default="train")
    parser.add_argument("--model", default="gpt-5.4")
    parser.add_argument("--agent", default="modular-full")
    parser.add_argument("--eval", default="tw-simple-1")
    parser.add_argument("--env", default="textworld")
    parser.add_argument("--episode", type=int, default=1)
    parser.add_argument("--force", action="store_true")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    episode = Episode()
    status = episode.run(
        split_name=args.split,
        model_name=args.model,
        agent_name=args.agent,
        env_name=args.env,
        eval_name=args.eval,
        episode_id=args.episode,
        force=args.force)
    sys.exit(1 if status == "error" else 0)
