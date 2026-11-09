"""Style and constraints validator for repository requirements."""

import ast
import os
import unittest

MAX_LINE_LENGTH = 79
MAX_FUNCTION_LINES = 40
MAX_FUNCTION_ARGS = 7
ZERO_LENGTH = 0


class CodeStyleTest(unittest.TestCase):
    """Verify that source code complies with all repository rules."""

    def _get_py_files(self, directory: str):
        """Yield paths of all python files in given directory."""
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    yield os.path.join(root, file)

    def test_line_lengths_in_src(self):
        """Check that no lines in src exceed maximum allowed length."""
        for file_path in self._get_py_files("src"):
            with open(file_path, "r", encoding="utf-8") as file:
                for line_idx, line in enumerate(file, start=1):
                    stripped = line.rstrip("\r\n")
                    self.assertLessEqual(
                        len(stripped),
                        MAX_LINE_LENGTH,
                        f"Line {line_idx} in {file_path} exceeds length: "
                        f"{len(stripped)} > {MAX_LINE_LENGTH}",
                    )

    def test_function_lengths_and_args_in_src(self):
        """Check function length and argument count limits in src."""
        for file_path in self._get_py_files("src"):
            with open(file_path, "r", encoding="utf-8") as file:
                tree = ast.parse(file.read(), filename=file_path)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_len = node.end_lineno - node.lineno + 1
                    self.assertLessEqual(
                        func_len,
                        MAX_FUNCTION_LINES,
                        f"Function {node.name} in {file_path} has {func_len} "
                        f"lines (> {MAX_FUNCTION_LINES})",
                    )
                    arg_count = len(node.args.args)
                    self.assertLessEqual(
                        arg_count,
                        MAX_FUNCTION_ARGS,
                        f"Function {node.name} in {file_path} has "
                        f"{arg_count} args (> {MAX_FUNCTION_ARGS})",
                    )

    def test_no_inline_comments_in_src(self):
        """Verify no hash comments are used instead of docstrings."""
        for file_path in self._get_py_files("src"):
            with open(file_path, "r", encoding="utf-8") as file:
                for line_idx, line in enumerate(file, start=1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        self.fail(
                            f"Comment found on line {line_idx} in {file_path}:"
                            f" '{stripped}'. Use docstrings per rule K1."
                        )


if __name__ == "__main__":
    unittest.main()
