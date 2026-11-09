"""Command line entrypoint for dependency graph visualizer."""

import argparse
import sys
from src.config import ConfigError, load_config

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
STAGE_ONE = 1
DEFAULT_CONFIG_PATH = "config.ini"


def parse_arguments(argv: list) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Dependency visualizer for Ubuntu packages (Variant 23)."
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config_path",
        default=DEFAULT_CONFIG_PATH,
        help="Path to INI configuration file.",
    )
    parser.add_argument(
        "-s",
        "--stage",
        dest="stage",
        type=int,
        default=STAGE_ONE,
        choices=[1, 2, 3, 4, 5],
        help="Stage of assignment to execute (1-5).",
    )
    return parser.parse_args(argv)


def run_stage_one(config_path: str) -> int:
    """Execute Stage 1: Load config and display all parameters."""
    cfg = load_config(config_path)
    for key, val in cfg.to_dict().items():
        print(f"{key}: {val}")
    return EXIT_SUCCESS


def main(argv: list = None) -> int:
    """Main application routine."""
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = parse_arguments(argv)
        if args.stage == STAGE_ONE:
            return run_stage_one(args.config_path)
        return EXIT_SUCCESS
    except ConfigError as err:
        sys.stderr.write(f"Configuration Error: {err}\n")
        return EXIT_FAILURE
    except Exception as exc:
        sys.stderr.write(f"Unexpected Error: {exc}\n")
        return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())
