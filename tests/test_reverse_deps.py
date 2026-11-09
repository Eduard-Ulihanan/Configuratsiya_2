"""Unit tests for Stage 4 reverse dependency calculation using BFS."""

import os
import tempfile
import unittest
from src.main import EXIT_SUCCESS, main
from src.reverse_deps import get_reverse_dependencies, invert_graph

ZERO_DEPS = 0
EXPECTED_REV_LINEAR = 2


class ReverseDepsTest(unittest.TestCase):
    """Test suite for reverse dependency computation."""

    def setUp(self):
        """Prepare temporary directory for test configs."""
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_invert_graph_structure(self):
        """Verify inversion of directed graph edges."""
        repo = {"A": ["B", "C"], "B": ["D"], "C": [], "D": []}
        inverted = invert_graph(repo)
        self.assertIn("A", inverted["B"])
        self.assertIn("A", inverted["C"])
        self.assertIn("B", inverted["D"])
        self.assertEqual(len(inverted["A"]), ZERO_DEPS)

    def test_linear_reverse_dependencies(self):
        """Verify reverse dependencies in linear chain A -> B -> C."""
        repo = {"A": ["B"], "B": ["C"], "C": []}
        direct, all_rev = get_reverse_dependencies("C", repo)
        self.assertEqual(direct, ["B"])
        self.assertEqual(len(all_rev), EXPECTED_REV_LINEAR)
        self.assertIn("B", all_rev)
        self.assertIn("A", all_rev)

    def test_diamond_reverse_dependencies(self):
        """Verify reverse dependencies in diamond DAG."""
        repo = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        direct, all_rev = get_reverse_dependencies("D", repo)
        self.assertIn("B", direct)
        self.assertIn("C", direct)
        self.assertIn("A", all_rev)

    def test_cyclic_reverse_dependencies(self):
        """Verify reverse dependencies with cycles without infinite loop."""
        repo = {"A": ["B"], "B": ["C"], "C": ["A"]}
        direct, all_rev = get_reverse_dependencies("A", repo)
        self.assertEqual(direct, ["C"])
        self.assertIn("B", all_rev)
        self.assertIn("C", all_rev)

    def test_reverse_dependencies_filtered(self):
        """Verify that packages containing filter substring are excluded."""
        repo = {
            "A_EXCLUDE": ["C"],
            "B": ["C"],
            "C": [],
        }
        direct, all_rev = get_reverse_dependencies(
            "C",
            repo,
            filter_substr="_EXCLUDE",
        )
        self.assertEqual(direct, ["B"])
        self.assertNotIn("A_EXCLUDE", all_rev)

    def test_cli_stage_four_execution(self):
        """Verify Stage 4 CLI runs and reports reverse dependencies."""
        repo_file = os.path.join(self.temp_dir.name, "graph.txt")
        with open(repo_file, "w", encoding="utf-8") as file:
            file.write("A: B\nB: C\nC:\n")

        ini_content = (
            f"[settings]\n"
            f"package_name = C\n"
            f"repo_url = {repo_file}\n"
            f"test_mode = true\n"
            f"output_image = out.svg\n"
            f"filter_substring = none\n"
        )
        ini_file = os.path.join(self.temp_dir.name, "config.ini")
        with open(ini_file, "w", encoding="utf-8") as file:
            file.write(ini_content)

        code = main(["--config", ini_file, "--stage", "4"])
        self.assertEqual(code, EXIT_SUCCESS)


if __name__ == "__main__":
    unittest.main()
