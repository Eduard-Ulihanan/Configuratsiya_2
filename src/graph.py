"""Dependency graph builder using recursive BFS traversal."""

import os
import re
from typing import Dict, List, Set

EMPTY_LEN = 0
COLON_DELIM = ":"
ARROW_DELIM = "->"
COMMA_DELIM = ","
SPLIT_ONCE = 1


def parse_test_repository(content: str) -> Dict[str, List[str]]:
    """Parse test repository file where packages are capital letters."""
    repo: Dict[str, List[str]] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if ARROW_DELIM in line:
            parts = line.split(ARROW_DELIM, SPLIT_ONCE)
        elif COLON_DELIM in line:
            parts = line.split(COLON_DELIM, SPLIT_ONCE)
        else:
            continue
        node = parts[EMPTY_LEN].strip()
        if not node:
            continue
        deps = []
        raw_deps = parts[SPLIT_ONCE].strip()
        if raw_deps:
            for item in raw_deps.replace(COMMA_DELIM, " ").split():
                clean_item = item.strip()
                if clean_item and clean_item not in deps:
                    deps.append(clean_item)
        repo[node] = deps
    return repo


def load_repository_data(
    repo_url: str,
    test_mode: bool,
) -> Dict[str, List[str]]:
    """Load package data from test repository file or APT repository."""
    if test_mode:
        with open(repo_url, "r", encoding="utf-8") as file:
            return parse_test_repository(file.read())
    from src.apt_parser import fetch_repository_text, parse_packages_index

    text = fetch_repository_text(repo_url)
    return parse_packages_index(text)


def _bfs_recursive_step(
    queue: List[str],
    visited: Set[str],
    graph: Dict[str, List[str]],
    repo: Dict[str, List[str]],
    filter_substr: str,
) -> Dict[str, List[str]]:
    """Execute single BFS step recursively until queue is empty."""
    if len(queue) == EMPTY_LEN:
        return graph

    current = queue.pop(EMPTY_LEN)
    raw_deps = repo.get(current, [])
    filtered_deps = []
    for dep in raw_deps:
        if filter_substr and filter_substr in dep:
            continue
        filtered_deps.append(dep)

    graph[current] = filtered_deps
    for dep in filtered_deps:
        if dep not in visited:
            visited.add(dep)
            queue.append(dep)

    return _bfs_recursive_step(
        queue,
        visited,
        graph,
        repo,
        filter_substr,
    )


def build_dependency_graph(
    start_package: str,
    repo: Dict[str, List[str]],
    filter_substr: str = "",
) -> Dict[str, List[str]]:
    """Build dependency graph starting from root package via recursive BFS."""
    if start_package not in repo:
        raise KeyError(f"Package '{start_package}' not found in repository.")
    visited = {start_package}
    queue = [start_package]
    graph: Dict[str, List[str]] = {}
    return _bfs_recursive_step(
        queue,
        visited,
        graph,
        repo,
        filter_substr,
    )


def detect_cycles(graph: Dict[str, List[str]]) -> List[List[str]]:
    """Detect cycles in the directed dependency graph."""
    cycles: List[List[str]] = []
    visited: Set[str] = set()
    stack: List[str] = []

    def _dfs(node: str):
        visited.add(node)
        stack.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                _dfs(neighbor)
            elif neighbor in stack:
                cycle_start = stack.index(neighbor)
                cycles.append(stack[cycle_start:] + [neighbor])
        stack.pop()

    for node in graph:
        if node not in visited:
            _dfs(node)
    return cycles
