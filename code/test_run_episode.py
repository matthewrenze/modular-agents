from run_episode import build_parser


class TestRunEpisode:

    def test_parser_defaults_match_smoke_config(self):
        args = build_parser().parse_args([])
        assert args.split == "train"
        assert args.model == "gpt-5.4"
        assert args.agent == "modular-full"
        assert args.eval == "tw-simple-1"
        assert args.env == "textworld"
        assert args.episode == 1
        assert args.force is False
