"""Command line entrypoint for dependency graph visualizer."""

import argparse
import sys
from src.apt_parser import (
    PackageNotFoundError,
    fetch_repository_text,
    get_direct_dependencies,
    parse_packages_index,
)
from src.config import ConfigError, load_config
from src.graph import (
    build_dependency_graph,
    detect_cycles,
    load_repository_data,
)
from src.reverse_deps import get_reverse_dependencies

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
STAGE_ONE = 1
STAGE_TWO = 2
STAGE_THREE = 3
STAGE_FOUR = 4
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


def run_stage_two(config_path: str) -> int:
    """Execute Stage 2: Extract and display direct dependencies."""
    cfg = load_config(config_path)
    content = fetch_repository_text(cfg.repo_url)
    repo = parse_packages_index(content)
    direct_deps = get_direct_dependencies(cfg.package_name, repo)
    print(f"Direct dependencies for {cfg.package_name}:")
    for dep in direct_deps:
        print(f"  - {dep}")
    return EXIT_SUCCESS


def run_stage_three(config_path: str) -> int:
    """Execute Stage 3: Build transitive dependency graph with BFS."""
    cfg = load_config(config_path)
    repo = load_repository_data(cfg.repo_url, cfg.test_mode)
    graph = build_dependency_graph(
        cfg.package_name,
        repo,
        cfg.filter_substring,
    )
    print(f"Transitive dependency graph for {cfg.package_name} (BFS):")
    for node, deps in graph.items():
        print(f"  {node} -> {deps}")
    cycles = detect_cycles(graph)
    if cycles:
        print(f"Cycles detected: {cycles}")
    else:
        print("Cycles detected: None")
    return EXIT_SUCCESS


def run_stage_four(config_path: str) -> int:
    """Execute Stage 4: Output reverse dependencies for target package."""
    cfg = load_config(config_path)
    repo = load_repository_data(cfg.repo_url, cfg.test_mode)
    direct_rev, all_rev = get_reverse_dependencies(
        cfg.package_name,
        repo,
        cfg.filter_substring,
    )
    print(f"Reverse dependencies for {cfg.package_name}:")
    print(f"  Direct reverse: {direct_rev}")
    print(f"  All (transitive) reverse: {all_rev}")
    return EXIT_SUCCESS


def main(argv: list = None) -> int:
    """Main application routine."""
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = parse_arguments(argv)
        if args.stage == STAGE_ONE:
            return run_stage_one(args.config_path)
        if args.stage == STAGE_TWO:
            return run_stage_two(args.config_path)
        if args.stage == STAGE_THREE:
            return run_stage_three(args.config_path)
        if args.stage == STAGE_FOUR:
            return run_stage_four(args.config_path)
        return EXIT_SUCCESS
    except ConfigError as err:
        sys.stderr.write(f"Configuration Error: {err}\n")
        return EXIT_FAILURE
    except (PackageNotFoundError, KeyError) as err:
        sys.stderr.write(f"Package Error: {err}\n")
        return EXIT_FAILURE
    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())
