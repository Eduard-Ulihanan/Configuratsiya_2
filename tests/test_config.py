"""Unit tests for configuration parser and Stage 1 error handling."""

import os
import tempfile
import unittest
from src.config import AppConfig, ConfigError, load_config
from src.main import EXIT_FAILURE, EXIT_SUCCESS, main

ZERO_DIFF = 0


class ConfigParserTest(unittest.TestCase):
    """Test suite verifying validation and error handling for all params."""

    def setUp(self):
        """Prepare temporary directory for test config files."""
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def _create_ini(self, content: str) -> str:
        """Create a temporary INI configuration file."""
        file_path = os.path.join(self.temp_dir.name, "config.ini")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        return file_path

    def test_valid_config_loading(self):
        """Verify successful loading of valid configuration."""
        content = (
            "[settings]\n"
            "package_name = curl\n"
            "repo_url = https://example.com/Packages.gz\n"
            "test_mode = false\n"
            "output_image = out.svg\n"
            "filter_substring = test\n"
        )
        path = self._create_ini(content)
        cfg = load_config(path)
        self.assertEqual(cfg.package_name, "curl")
        self.assertEqual(cfg.repo_url, "https://example.com/Packages.gz")
        self.assertFalse(cfg.test_mode)
        self.assertEqual(cfg.output_image, "out.svg")
        self.assertEqual(cfg.filter_substring, "test")

    def test_missing_config_file_raises_error(self):
        """Verify error when config file path does not exist."""
        with self.assertRaises(ConfigError):
            load_config("non_existent_file_path.ini")

    def test_missing_section_raises_error(self):
        """Verify error when INI has no recognized section."""
        path = self._create_ini("key = value\n")
        with self.assertRaises(ConfigError):
            load_config(path)

    def test_missing_parameter_raises_error(self):
        """Verify error when required parameter is omitted."""
        content = (
            "[settings]\n"
            "package_name = curl\n"
            "repo_url = https://example.com/Packages.gz\n"
            "test_mode = false\n"
            "output_image = out.svg\n"
        )
        path = self._create_ini(content)
        with self.assertRaises(ConfigError) as ctx:
            load_config(path)
        self.assertIn("filter_substring", str(ctx.exception))

    def test_invalid_package_name_empty(self):
        """Verify error when package_name is empty."""
        content = (
            "[settings]\n"
            "package_name =   \n"
            "repo_url = https://example.com/Packages.gz\n"
            "test_mode = false\n"
            "output_image = out.svg\n"
            "filter_substring = none\n"
        )
        path = self._create_ini(content)
        with self.assertRaises(ConfigError) as ctx:
            load_config(path)
        self.assertIn("package_name cannot be empty", str(ctx.exception))

    def test_invalid_package_name_characters(self):
        """Verify error when package_name contains invalid characters."""
        content = (
            "[settings]\n"
            "package_name = curl;rm -rf /\n"
            "repo_url = https://example.com/Packages.gz\n"
            "test_mode = false\n"
            "output_image = out.svg\n"
            "filter_substring = none\n"
        )
        path = self._create_ini(content)
        with self.assertRaises(ConfigError) as ctx:
            load_config(path)
        self.assertIn("Invalid package_name", str(ctx.exception))

    def test_invalid_test_mode_boolean(self):
        """Verify error when test_mode is not a valid boolean."""
        content = (
            "[settings]\n"
            "package_name = curl\n"
            "repo_url = https://example.com/Packages.gz\n"
            "test_mode = not_a_boolean\n"
            "output_image = out.svg\n"
            "filter_substring = none\n"
        )
        path = self._create_ini(content)
        with self.assertRaises(ConfigError) as ctx:
            load_config(path)
        self.assertIn("Expected boolean", str(ctx.exception))

    def test_invalid_repo_url_format(self):
        """Verify error when repo_url is neither valid URL nor file."""
        content = (
            "[settings]\n"
            "package_name = curl\n"
            "repo_url = ftp://invalid.host/file\n"
            "test_mode = false\n"
            "output_image = out.svg\n"
            "filter_substring = none\n"
        )
        path = self._create_ini(content)
        with self.assertRaises(ConfigError) as ctx:
            load_config(path)
        self.assertIn("Invalid repo_url", str(ctx.exception))

    def test_test_mode_missing_repo_file(self):
        """Verify error when test_mode is true and file does not exist."""
        content = (
            "[settings]\n"
            "package_name = A\n"
            "repo_url = missing_graph_file.txt\n"
            "test_mode = true\n"
            "output_image = out.svg\n"
            "filter_substring = none\n"
        )
        path = self._create_ini(content)
        with self.assertRaises(ConfigError) as ctx:
            load_config(path)
        self.assertIn("Test repository file does not exist", str(ctx.exception))

    def test_invalid_output_image_extension(self):
        """Verify error when output_image does not end with .svg."""
        content = (
            "[settings]\n"
            "package_name = curl\n"
            "repo_url = https://example.com/Packages.gz\n"
            "test_mode = false\n"
            "output_image = out.png\n"
            "filter_substring = none\n"
        )
        path = self._create_ini(content)
        with self.assertRaises(ConfigError) as ctx:
            load_config(path)
        self.assertIn(".svg", str(ctx.exception))

    def test_main_cli_stage_one_success(self):
        """Verify CLI execution for Stage 1 printing key-value pairs."""
        content = (
            "[settings]\n"
            "package_name = curl\n"
            "repo_url = https://example.com/Packages.gz\n"
            "test_mode = false\n"
            "output_image = out.svg\n"
            "filter_substring = test\n"
        )
        path = self._create_ini(content)
        code = main(["--config", path, "--stage", "1"])
        self.assertEqual(code, EXIT_SUCCESS)

    def test_main_cli_invalid_config_exits_failure(self):
        """Verify CLI exits with failure on invalid config."""
        code = main(["--config", "non_existent.ini", "--stage", "1"])
        self.assertEqual(code, EXIT_FAILURE)


if __name__ == "__main__":
    unittest.main()
