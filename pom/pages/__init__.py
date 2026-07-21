"""
Page Object Model pages package.
Exports all page object classes.
"""

from pom.pages.base_page import BasePageObject, UIElement
from pom.pages.chat_page import ChatPage
from pom.pages.health_page import HealthPage
from pom.pages.settings_page import SettingsPage

__all__ = [
    "BasePageObject",
    "UIElement",
    "ChatPage",
    "HealthPage",
    "SettingsPage"
]