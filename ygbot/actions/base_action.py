"""
Base Action Interface for the Action Sequencer pattern.

Actions represent discrete gameplay steps executed on specific pages.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from ..core.utils import log, Colors


class BaseAction(ABC):
    """
    Abstract Action defining contract for executing discrete page interactions.
    """

    def __init__(self, page: Any):
        self.page = page

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the action."""
        pass

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Executes the action on the associated page."""
        pass
