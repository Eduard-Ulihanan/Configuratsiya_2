"""Ubuntu APT Packages index parser for direct dependency extraction."""

import gzip
import os
import re
import urllib.request
from typing import Dict, List

EMPTY_COUNT = 0
FIRST_INDEX = 0
GZIP_HEADER_SIZE = 2
GZIP_MAGIC_FIRST = 0x1F
GZIP_MAGIC_SECOND = 0x8B
COLON_DELIMITER = ":"
COMMA_DELIMITER = ","
PIPE_DELIMITER = "|"
PACKAGE_HEADER = "package:"
DEPENDS_HEADER = "depends:"


class PackageNotFoundError(Exception):
    """Raised when specified package is not present in repository."""


def _is_gzipped(data: bytes) -> bool:
    """Check if byte sequence starts with gzip magic header."""
    if len(data) < GZIP_HEADER_SIZE:
        return False
    return (
        data[FIRST_INDEX] == GZIP_MAGIC_FIRST
        and data[FIRST_INDEX + 1] == GZIP_MAGIC_SECOND
    )


def _load_raw_data(url_or_path: str) -> bytes:
    """Load raw bytes from an HTTP URL or local file path."""
    if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
        req = urllib.request.Request(
            url_or_path,
            headers={"User-Agent": "AptVisualizer/1.0"},
        )
        with urllib.request.urlopen(req) as response:
            return response.read()
    if not os.path.exists(url_or_path):
        raise FileNotFoundError(f"File not found: {url_or_path}")
    with open(url_or_path, "rb") as file:
        return file.read()


def fetch_repository_text(url_or_path: str) -> str:
    """Fetch and decompress APT Packages index content."""
    raw_data = _load_raw_data(url_or_path)
    if _is_gzipped(raw_data):
        decompressed = gzip.decompress(raw_data)
        return decompressed.decode("utf-8", errors="replace")
    return raw_data.decode("utf-8", errors="replace")


def clean_dependency_name(raw_token: str) -> str:
    """Clean single dependency token removing version and architecture."""
    token = raw_token.strip()
    if not token:
        return ""
    if PIPE_DELIMITER in token:
        token = token.split(PIPE_DELIMITER)[FIRST_INDEX].strip()
    token = re.sub(r"\(.*?\)", "", token).strip()
    if COLON_DELIMITER in token:
        token = token.split(COLON_DELIMITER)[FIRST_INDEX].strip()
    return token


def parse_depends_field(raw_depends: str) -> List[str]:
    """Parse Depends header string into a list of package names."""
    if not raw_depends:
        return []
    dependencies = []
    tokens = raw_depends.split(COMMA_DELIMITER)
    for token in tokens:
        cleaned = clean_dependency_name(token)
        if cleaned and cleaned not in dependencies:
            dependencies.append(cleaned)
    return dependencies


def _parse_single_stanza(stanza: str) -> tuple:
    """Extract package name and depends list from single stanza string."""
    pkg_name = ""
    depends_lines = []
    collecting_depends = False
    for line in stanza.splitlines():
        if line.lower().startswith(PACKAGE_HEADER):
            pkg_name = line.split(COLON_DELIMITER, 1)[1].strip()
            collecting_depends = False
        elif line.lower().startswith(DEPENDS_HEADER):
            depends_lines.append(line.split(COLON_DELIMITER, 1)[1].strip())
            collecting_depends = True
        elif collecting_depends and line.startswith((" ", "\t")):
            depends_lines.append(line.strip())
        else:
            collecting_depends = False
    all_depends_str = " ".join(depends_lines)
    return pkg_name, parse_depends_field(all_depends_str)


def parse_packages_index(content: str) -> Dict[str, List[str]]:
    """Parse entire APT Packages text into dictionary of dependencies."""
    result: Dict[str, List[str]] = {}
    stanzas = re.split(r"\n\s*\n", content)
    for stanza in stanzas:
        if not stanza.strip():
            continue
        pkg_name, deps = _parse_single_stanza(stanza)
        if pkg_name and pkg_name not in result:
            result[pkg_name] = deps
    return result


def get_direct_dependencies(
    package_name: str,
    repository: Dict[str, List[str]],
) -> List[str]:
    """Retrieve direct dependencies for a package or raise error."""
    if package_name not in repository:
        raise PackageNotFoundError(
            f"Package '{package_name}' not found in repository."
        )
    return repository[package_name]
