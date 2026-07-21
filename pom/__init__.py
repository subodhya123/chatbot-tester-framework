"""
Page Object Model package for ChatBot Tester Framework.
Provides structured approach to chatbot testing with reusable page objects.
"""

from typing import Any

from pom.pages.base_page import BasePageObject, UIElement
from pom.pages.chat_page import ChatPage
from pom.pages.health_page import HealthPage
from pom.pages.settings_page import SettingsPage

__all__ = [
    "BasePageObject",
    "UIElement",
    "ChatPage",
    "HealthPage",
    "SettingsPage",
    "create_page_object",
    "create_all_pages"
]


def create_page_object(page_type: str, driver: Any = None, base_url: str = "", **kwargs):
    """
    Factory function to create page objects by type.

    Args:
        page_type: Type of page object ("chat", "health", "settings")
        driver: Optional driver instance
        base_url: Base URL for the application
        **kwargs: Additional arguments for specific page types

    Returns:
        Page object instance

    Raises:
        ValueError: If page_type is not recognized
    """
    page_types = {
        "chat": ChatPage,
        "health": HealthPage,
        "settings": SettingsPage
    }

    page_class = page_types.get(page_type.lower())

    if page_class is None:
        available = ", ".join(page_types.keys())
        raise ValueError(
            f"Unknown page type: '{page_type}'. Available types: {available}"
        )

    return page_class(driver=driver, base_url=base_url, **kwargs)


def create_all_pages(driver: Any = None, base_url: str = ""):
    """
    Create instances of all page objects.

    Args:
        driver: Optional driver instance
        base_url: Base URL for the application

    Returns:
        Dictionary mapping page names to page objects
    """
    return {
        "chat": ChatPage(driver=driver, base_url=base_url),
        "health": HealthPage(driver=driver, base_url=base_url),
        "settings": SettingsPage(driver=driver, base_url=base_url)
    }