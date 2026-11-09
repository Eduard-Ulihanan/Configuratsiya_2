"""Configuration parser and validator for dependency visualizer."""

import configparser
import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

EMPTY_LEN = 0
SECTION_NAME = "settings"
SVG_EXTENSION = ".svg"
ALLOWED_PKG_PATTERN = r"^[a-zA-Z0-9][a-zA-Z0-9_\.\-\+]*$"
TRUE_LITERALS = ("true", "1", "yes", "on")
FALSE_LITERALS = ("false", "0", "no", "off")
HTTP_SCHEMES = ("http", "https")


class ConfigError(Exception):
    """Raised when configuration file or value is invalid."""


@dataclass(frozen=True)
class AppConfig:
    """Strongly typed application configuration."""

    package_name: str
    repo_url: str
    test_mode: bool
    output_image: str
    filter_substring: str

    def to_dict(self) -> dict:
        """Convert configuration options to dictionary for display."""
        return {
            "package_name": self.package_name,
            "repo_url": self.repo_url,
            "test_mode": str(self.test_mode).lower(),
            "output_image": self.output_image,
            "filter_substring": self.filter_substring,
        }


def _read_ini(file_path: str) -> configparser.ConfigParser:
    """Read INI file from disk and return parser instance."""
    if not os.path.exists(file_path):
        raise ConfigError(f"Config file not found: {file_path}")
    parser = configparser.ConfigParser()
    try:
        parser.read(file_path, encoding="utf-8")
    except configparser.Error as error:
        raise ConfigError(f"Failed to parse INI config: {error}") from error
    return parser


def _get_section(parser: configparser.ConfigParser) -> dict:
    """Retrieve settings section as dictionary."""
    if parser.has_section(SECTION_NAME):
        return dict(parser.items(SECTION_NAME))
    sections = parser.sections()
    if len(sections) == EMPTY_LEN:
        if parser.defaults():
            return dict(parser.defaults())
        raise ConfigError(f"Config has no sections; expected [{SECTION_NAME}]")
    return dict(parser.items(sections[EMPTY_LEN]))


def _validate_package_name(name: str) -> str:
    """Validate package name parameter."""
    cleaned = name.strip()
    if len(cleaned) == EMPTY_LEN:
        raise ConfigError("package_name cannot be empty")
    if not re.match(ALLOWED_PKG_PATTERN, cleaned):
        raise ConfigError(f"Invalid package_name value: {cleaned}")
    return cleaned


def _validate_test_mode(raw: str) -> bool:
    """Validate and convert test_mode boolean parameter."""
    cleaned = raw.strip().lower()
    if cleaned in TRUE_LITERALS:
        return True
    if cleaned in FALSE_LITERALS:
        return False
    raise ConfigError(
        f"Invalid test_mode value: '{raw}'. Expected boolean true/false."
    )


def _validate_repo_url(url: str, test_mode: bool) -> str:
    """Validate repo_url or path to test repository."""
    cleaned = url.strip()
    if len(cleaned) == EMPTY_LEN:
        raise ConfigError("repo_url cannot be empty")
    if test_mode:
        if not os.path.exists(cleaned):
            raise ConfigError(
                f"Test repository file does not exist: {cleaned}"
            )
        return cleaned
    parsed = urlparse(cleaned)
    if parsed.scheme in HTTP_SCHEMES and parsed.netloc:
        return cleaned
    if os.path.exists(cleaned):
        return cleaned
    raise ConfigError(
        f"Invalid repo_url: '{cleaned}'. Must be HTTP/HTTPS or existing file."
    )


def _validate_output_image(path: str) -> str:
    """Validate output image path."""
    cleaned = path.strip()
    if len(cleaned) == EMPTY_LEN:
        raise ConfigError("output_image cannot be empty")
    if not cleaned.lower().endswith(SVG_EXTENSION):
        raise ConfigError(
            f"output_image must end with {SVG_EXTENSION}: {cleaned}"
        )
    return cleaned


def _validate_filter_substring(substring: str) -> str:
    """Validate filter substring parameter."""
    cleaned = substring.strip()
    if "\n" in cleaned or "\r" in cleaned:
        raise ConfigError("filter_substring cannot contain newlines")
    return cleaned


def load_config(file_path: str) -> AppConfig:
    """Load and validate all parameters from an INI file."""
    parser = _read_ini(file_path)
    section = _get_section(parser)
    required_keys = (
        "package_name",
        "repo_url",
        "test_mode",
        "output_image",
        "filter_substring",
    )
    for key in required_keys:
        if key not in section:
            raise ConfigError(f"Missing required parameter: {key}")

    test_mode = _validate_test_mode(section["test_mode"])
    package_name = _validate_package_name(section["package_name"])
    repo_url = _validate_repo_url(section["repo_url"], test_mode)
    output_image = _validate_output_image(section["output_image"])
    filter_substring = _validate_filter_substring(
        section["filter_substring"]
    )

    return AppConfig(
        package_name=package_name,
        repo_url=repo_url,
        test_mode=test_mode,
        output_image=output_image,
        filter_substring=filter_substring,
    )
