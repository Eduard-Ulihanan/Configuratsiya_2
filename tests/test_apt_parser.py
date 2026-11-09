"""Unit tests for Ubuntu APT Packages index parser."""

import gzip
import os
import tempfile
import unittest
from src.apt_parser import (
    PackageNotFoundError,
    clean_dependency_name,
    fetch_repository_text,
    get_direct_dependencies,
    parse_depends_field,
    parse_packages_index,
)
from src.main import EXIT_FAILURE, EXIT_SUCCESS, main

ZERO_COUNT = 0
EXPECTED_DEP_COUNT = 3


class AptParserTest(unittest.TestCase):
    """Test suite for APT repository parsing logic."""

    def setUp(self):
        """Set up temporary working directory."""
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_clean_dependency_name(self):
        """Verify token cleanup with version and arch qualifier."""
        self.assertEqual(clean_dependency_name("libc6 (>= 2.34)"), "libc6")
        self.assertEqual(
            clean_dependency_name("default-mta | mail-transport-agent"),
            "default-mta",
        )
        self.assertEqual(
            clean_dependency_name("perl:any (>= 5.20)"),
            "perl",
        )

    def test_parse_depends_field(self):
        """Verify parsing raw Depends header into distinct names."""
        raw = "libc6 (>= 2.34), libcurl4 (= 7.81.0), zlib1g (>= 1:1.1.4)"
        deps = parse_depends_field(raw)
        self.assertEqual(len(deps), EXPECTED_DEP_COUNT)
        self.assertEqual(deps, ["libc6", "libcurl4", "zlib1g"])

    def test_parse_packages_index_plain(self):
        """Verify parsing raw Packages index content."""
        content = (
            "Package: curl\n"
            "Version: 7.81.0-1\n"
            "Depends: libc6 (>= 2.34), libcurl4\n"
            "\n"
            "Package: libc6\n"
            "Version: 2.35-0\n"
            "Depends: libgcc-s1\n"
            "\n"
            "Package: libgcc-s1\n"
            "Version: 12-2022\n"
        )
        repo = parse_packages_index(content)
        self.assertIn("curl", repo)
        self.assertIn("libc6", repo)
        self.assertIn("libgcc-s1", repo)
        self.assertEqual(repo["curl"], ["libc6", "libcurl4"])
        self.assertEqual(repo["libgcc-s1"], [])

    def test_fetch_gzipped_repository_file(self):
        """Verify decompressing gzipped repository file."""
        content = "Package: nano\nDepends: libc6\n\n"
        gz_path = os.path.join(self.temp_dir.name, "Packages.gz")
        with gzip.open(gz_path, "wb") as file:
            file.write(content.encode("utf-8"))

        text = fetch_repository_text(gz_path)
        repo = parse_packages_index(text)
        self.assertEqual(get_direct_dependencies("nano", repo), ["libc6"])

    def test_get_direct_dependencies_missing_package(self):
        """Verify PackageNotFoundError on non-existent package."""
        repo = {"curl": ["libc6"]}
        with self.assertRaises(PackageNotFoundError):
            get_direct_dependencies("unknown-pkg", repo)

    def test_main_cli_stage_two_success(self):
        """Verify Stage 2 execution prints direct dependencies."""
        pkg_content = "Package: curl\nDepends: libc6, libcurl4\n\n"
        repo_file = os.path.join(self.temp_dir.name, "Packages")
        with open(repo_file, "w", encoding="utf-8") as file:
            file.write(pkg_content)

        ini_content = (
            f"[settings]\n"
            f"package_name = curl\n"
            f"repo_url = {repo_file}\n"
            f"test_mode = false\n"
            f"output_image = out.svg\n"
            f"filter_substring = none\n"
        )
        ini_file = os.path.join(self.temp_dir.name, "config.ini")
        with open(ini_file, "w", encoding="utf-8") as file:
            file.write(ini_content)

        code = main(["--config", ini_file, "--stage", "2"])
        self.assertEqual(code, EXIT_SUCCESS)

    def test_main_cli_stage_two_missing_package_fails(self):
        """Verify Stage 2 exits with failure if package not found."""
        pkg_content = "Package: bash\n\n"
        repo_file = os.path.join(self.temp_dir.name, "Packages")
        with open(repo_file, "w", encoding="utf-8") as file:
            file.write(pkg_content)

        ini_content = (
            f"[settings]\n"
            f"package_name = non_existent\n"
            f"repo_url = {repo_file}\n"
            f"test_mode = false\n"
            f"output_image = out.svg\n"
            f"filter_substring = none\n"
        )
        ini_file = os.path.join(self.temp_dir.name, "config.ini")
        with open(ini_file, "w", encoding="utf-8") as file:
            file.write(ini_content)

        code = main(["--config", ini_file, "--stage", "2"])
        self.assertEqual(code, EXIT_FAILURE)


if __name__ == "__main__":
    unittest.main()
