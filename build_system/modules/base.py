"""Base module definition for the static-site build system.

This module provides the BaseModule abstract base class that all build system
modules must inherit from.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any

class BaseModule(ABC):
    """Abstract base class for static-site builder modules."""

    def __init__(self, project_root: Path, config: Dict[str, Any]) -> None:
        """Initialize the module with the project root and config settings.

        Args:
            project_root: The root path of the project.
            config: A dictionary of configuration options.
        """
        self.project_root = project_root
        self.config = config

    @abstractmethod
    def run(self) -> bool:
        """Run the module's generation and validation logic.

        Returns:
            bool: True if completed successfully, False if critical errors occurred.
        """
        pass
