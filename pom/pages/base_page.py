"""
Base Page Object Model class for chatbot testing.
Provides common functionality for all page objects.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UIElement:
    """Represents a UI element with locator and metadata."""
    name: str
    locator_type: str  # "css", "xpath", "id", "name", "text"
    locator_value: str
    description: str = ""
    timeout: int = 30
    is_critical: bool = True


class BasePageObject(ABC):
    """
    Abstract base class for all Page Objects.
    Defines the common interface and functionality for POM pattern.
    """

    def __init__(self, driver: Any = None, base_url: str = ""):
        """
        Initialize the Page Object.

        Args:
            driver: Web/API driver instance
            base_url: Base URL for the application under test
        """
        self.driver = driver
        self.base_url = base_url.rstrip("/") if base_url else ""
        self._elements: Dict[str, UIElement] = {}
        self._page_load_time: Optional[datetime] = None

    @abstractmethod
    def wait_for_page_load(self, timeout: int = 30) -> bool:
        """
        Wait for page to fully load.

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if page loaded successfully, False otherwise
        """
        pass

    @abstractmethod
    def is_page_loaded(self) -> bool:
        """
        Check if the page is currently loaded.

        Returns:
            True if page is loaded, False otherwise
        """
        pass

    def register_element(self, element: UIElement):
        """
        Register an element with the page object.

        Args:
            element: UIElement instance to register
        """
        self._elements[element.name] = element

    def get_element(self, name: str) -> Optional[UIElement]:
        """
        Get a registered element by name.

        Args:
            name: Element name

        Returns:
            UIElement or None if not found
        """
        return self._elements.get(name)

    def get_all_elements(self) -> Dict[str, UIElement]:
        """Get all registered elements."""
        return self._elements.copy()

    def validate_elements(self) -> Dict[str, bool]:
        """
        Validate that all critical elements exist on the page.

        Returns:
            Dictionary mapping element names to their existence status
        """
        results = {}
        for name, element in self._elements.items():
            if element.is_critical:
                try:
                    results[name] = self._check_element_exists(element)
                except Exception:
                    results[name] = False
        return results

    def _check_element_exists(self, element: UIElement) -> bool:
        """
        Check if an element exists on the page.
        Override in subclasses for specific implementation.

        Args:
            element: UIElement to check

        Returns:
            True if element exists, False otherwise
        """
        return True  # Default implementation

    def get_page_info(self) -> Dict[str, Any]:
        """
        Get information about the current page.

        Returns:
            Dictionary containing page metadata
        """
        return {
            "page_name": self.__class__.__name__,
            "url": self.base_url,
            "elements_count": len(self._elements),
            "load_time": self._page_load_time.isoformat() if self._page_load_time else None
        }

    def screenshot_on_error(self, error: Exception) -> Optional[str]:
        """
        Capture screenshot when an error occurs.
        Override in subclasses for specific implementation.

        Args:
            error: Exception that triggered the error

        Returns:
            Path to screenshot or None
        """
        return None

    def log_action(self, action: str, details: str = ""):
        """Log an action performed on this page."""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] {self.__class__.__name__}.{action}: {details}")