"""Filesystem utilities for the static-site build system.

This module provides functions for walking directory structures and normalizing
names for URL-safe usage.
"""

import re
from pathlib import Path
from typing import Set, List

def normalize_name(name: str) -> str:
    """Normalize a folder or file name into a lowercase URL slug.

    Converts characters to lowercase, replaces underscores, spaces, and duplicate
    dashes with a single dash, and removes leading/trailing dashes.

    Args:
        name: The string to normalize.

    Returns:
        The normalized URL-safe string.
    """
    normalized = name.lower()
    # Replace spaces and underscores with dashes
    normalized = re.sub(r'[\s_]+', '-', normalized)
    # Replace multiple consecutive dashes with a single dash
    normalized = re.sub(r'-+', '-', normalized)
    return normalized.strip('-')

def scan_files(directory: Path, ignored_dirs: Set[str]) -> List[Path]:
    """Recursively scan a directory for all files, skipping ignored directories.

    Args:
        directory: The folder path to scan.
        ignored_dirs: A set of directory names to ignore (case-insensitive).

    Returns:
        A list of Path objects for all discovered files.
    """
    files: List[Path] = []
    ignored_lower = {d.lower() for d in ignored_dirs}

    try:
        for item in directory.iterdir():
            if item.is_dir():
                # Skip hidden directories and explicitly ignored directories
                if item.name.startswith('.') or item.name.lower() in ignored_lower:
                    continue
                files.extend(scan_files(item, ignored_dirs))
            elif item.is_file():
                # Skip hidden files
                if item.name.startswith('.'):
                    continue
                files.append(item)
    except PermissionError:
        # Silently skip directories where we do not have read permissions
        pass

    return files
