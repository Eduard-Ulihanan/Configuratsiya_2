"""Unit tests for Stage 5 Graphviz DOT export and SVG visualization."""

import os
import tempfile
import unittest
from src.main import EXIT_SUCCESS, main
from src.visualizer import export_graph_visualization, generate_graphviz_dot

ZERO_FILES = 0


class VisualizerTest(unittest.TestCase):
    """Test suite for Graphviz DOT generation and SVG rendering."""

    def setUp(self):
        """Set up temporary working directory for test outputs."""
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_generate_graphviz_dot(self):
        """Verify DOT text format with digraph, nodes, and edges."""
        graph = {"curl": ["libc6", "libcurl4"], "libc6": []}
        dot = generate_graphviz_dot("curl", graph)
        self.assertIn('digraph "curl"', dot)
        self.assertIn('"curl" -> "libc6";', dot)
        self.assertIn('"curl" -> "libcurl4";', dot)
        self.assertIn('"libc6";', dot)

    def test_export_graph_visualization_svg_output(self):
        """Verify SVG and DOT file creation and SVG XML structure."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        svg_path = os.path.join(self.temp_dir.name, "output.svg")
        dot_path, out_svg = export_graph_visualization("A", graph, svg_path)

        self.assertTrue(os.path.exists(dot_path))
        self.assertTrue(os.path.exists(out_svg))

        with open(out_svg, "r", encoding="utf-8") as file:
            svg_content = file.read()
        self.assertTrue(svg_content.startswith("<svg"))
        self.assertTrue(svg_content.rstrip().endswith("</svg>"))
        self.assertIn("<rect", svg_content)
        self.assertIn("<text", svg_content)
        self.assertIn("<path", svg_content)
        self.assertIn("A", svg_content)
        self.assertIn("B", svg_content)

    def test_cli_stage_five_execution(self):
        """Verify Stage 5 CLI execution on test repository."""
        repo_file = os.path.join(self.temp_dir.name, "graph.txt")
        with open(repo_file, "w", encoding="utf-8") as file:
            file.write("A: B\nB: C\nC:\n")

        svg_out = os.path.join(self.temp_dir.name, "stage5_test.svg")
        ini_content = (
            f"[settings]\n"
            f"package_name = A\n"
            f"repo_url = {repo_file}\n"
            f"test_mode = true\n"
            f"output_image = {svg_out}\n"
            f"filter_substring = none\n"
        )
        ini_file = os.path.join(self.temp_dir.name, "config.ini")
        with open(ini_file, "w", encoding="utf-8") as file:
            file.write(ini_content)

        code = main(["--config", ini_file, "--stage", "5"])
        self.assertEqual(code, EXIT_SUCCESS)
        self.assertTrue(os.path.exists(svg_out))

    def test_three_distinct_packages_visualization(self):
        """Demonstrate visualization for three distinct packages."""
        sample_repo = (
            "Package: curl\nDepends: libc6, libcurl4\n\n"
            "Package: libcurl4\nDepends: libc6, zlib1g\n\n"
            "Package: git\nDepends: libc6, libz1\n\n"
            "Package: nano\nDepends: libc6, libncursesw6\n\n"
            "Package: libc6\n\n"
            "Package: zlib1g\n\n"
            "Package: libz1\n\n"
            "Package: libncursesw6\n\n"
        )
        pkg_file = os.path.join(self.temp_dir.name, "Packages")
        with open(pkg_file, "w", encoding="utf-8") as file:
            file.write(sample_repo)

        packages = ["curl", "git", "nano"]
        for pkg in packages:
            svg_file = os.path.join(self.temp_dir.name, f"{pkg}.svg")
            ini_content = (
                f"[settings]\n"
                f"package_name = {pkg}\n"
                f"repo_url = {pkg_file}\n"
                f"test_mode = false\n"
                f"output_image = {svg_file}\n"
                f"filter_substring = none\n"
            )
            ini_file = os.path.join(self.temp_dir.name, f"{pkg}.ini")
            with open(ini_file, "w", encoding="utf-8") as file:
                file.write(ini_content)

            code = main(["--config", ini_file, "--stage", "5"])
            self.assertEqual(code, EXIT_SUCCESS)
            self.assertTrue(os.path.exists(svg_file))


if __name__ == "__main__":
    unittest.main()
