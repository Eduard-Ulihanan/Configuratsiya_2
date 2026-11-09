"""Reverse dependency calculations using recursive BFS traversal."""

from typing import Dict, List, Tuple
from src.graph import build_dependency_graph


def invert_graph(repo: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Invert repository graph edges to point from dependency to dependent."""
    inverted: Dict[str, List[str]] = {pkg: [] for pkg in repo}
    for pkg, deps in repo.items():
        for dep in deps:
            if dep not in inverted:
                inverted[dep] = []
            if pkg not in inverted[dep]:
                inverted[dep].append(pkg)
    return inverted


def get_reverse_dependencies(
    target_package: str,
    repo: Dict[str, List[str]],
    filter_substr: str = "",
) -> Tuple[List[str], List[str]]:
    """Find direct and transitive reverse dependencies using BFS."""
    inverted_repo = invert_graph(repo)
    if target_package not in inverted_repo:
        inverted_repo[target_package] = []

    rev_graph = build_dependency_graph(
        target_package,
        inverted_repo,
        filter_substr,
    )
    direct_reverse = [
        pkg
        for pkg in inverted_repo.get(target_package, [])
        if not (filter_substr and filter_substr in pkg)
    ]
    all_reverse = [pkg for pkg in rev_graph if pkg != target_package]
    return direct_reverse, all_reverse
