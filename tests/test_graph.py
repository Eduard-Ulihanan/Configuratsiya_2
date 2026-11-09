"""Unit tests for Stage 3 recursive BFS dependency graph building."""

import os
import tempfile
import unittest
from src.graph import (
    build_dependency_graph,
    detect_cycles,
    load_repository_data,
    parse_test_repository,
)
from src.main import EXIT_SUCCESS, main

ZERO_CYCLES = 0
EXPECTED_NODES_DIAMOND = 4


class GraphTraversalTest(unittest.TestCase):
    """Test suite for graph building and cycle handling."""

    def setUp(self):
        """Prepare temporary directory for test configs."""
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_parse_test_repository_uppercase(self):
        """Verify parsing test repository with uppercase letters."""
        raw = "A: B, C\nB: D\nC:\nD:\n"
        repo = parse_test_repository(raw)
        self.assertEqual(repo["A"], ["B", "C"])
        self.assertEqual(repo["B"], ["D"])
        self.assertEqual(repo["C"], [])

    def test_bfs_linear_graph(self):
        """Verify recursive BFS on linear graph."""
        repo = {"A": ["B"], "B": ["C"], "C": []}
        graph = build_dependency_graph("A", repo)
        self.assertEqual(graph["A"], ["B"])
        self.assertEqual(graph["B"], ["C"])
        self.assertEqual(graph["C"], [])

    def test_bfs_diamond_graph(self):
        """Verify recursive BFS on diamond DAG."""
        repo = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        graph = build_dependency_graph("A", repo)
        self.assertEqual(len(graph), EXPECTED_NODES_DIAMOND)
        self.assertEqual(graph["A"], ["B", "C"])
        self.assertEqual(graph["D"], [])

    def test_bfs_cycle_handling(self):
        """Verify graceful termination when cyclic dependencies exist."""
        repo = {"A": ["B"], "B": ["C"], "C": ["A"]}
        graph = build_dependency_graph("A", repo)
        self.assertIn("A", graph)
        self.assertIn("B", graph)
        self.assertIn("C", graph)
        cycles = detect_cycles(graph)
        self.assertGreater(len(cycles), ZERO_CYCLES)

    def test_bfs_substring_filtering(self):
        """Verify exclusion of packages matching filter substring."""
        repo = {
            "A": ["B_IGNORE", "C"],
            "B_IGNORE": ["D"],
            "C": ["E"],
            "E": [],
        }
        graph = build_dependency_graph("A", repo, filter_substr="_IGNORE")
        self.assertEqual(graph["A"], ["C"])
        self.assertNotIn("B_IGNORE", graph)
        self.assertIn("C", graph)
        self.assertIn("E", graph)

    def test_main_cli_stage_three_test_mode(self):
        """Verify CLI Stage 3 execution with test repository."""
        repo_file = os.path.join(self.temp_dir.name, "graph.txt")
        with open(repo_file, "w", encoding="utf-8") as file:
            file.write("A: B\nB: C\nC:\n")

        ini_content = (
            f"[settings]\n"
            f"package_name = A\n"
            f"repo_url = {repo_file}\n"
            f"test_mode = true\n"
            f"output_image = out.svg\n"
            f"filter_substring = none\n"
        )
        ini_file = os.path.join(self.temp_dir.name, "config.ini")
        with open(ini_file, "w", encoding="utf-8") as file:
            file.write(ini_content)

        code = main(["--config", ini_file, "--stage", "3"])
        self.assertEqual(code, EXIT_SUCCESS)


if __name__ == "__main__":
    unittest.main()
