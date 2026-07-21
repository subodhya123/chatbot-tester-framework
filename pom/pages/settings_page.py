"""
Settings Page Object - POM for chatbot settings and configuration.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pom.pages.base_page import BasePageObject, UIElement


class SettingsPage(BasePageObject):
    """
    Page Object for chatbot settings and configuration interface.
    Provides methods for modifying and verifying chatbot settings.
    """

    def __init__(self, driver: Any = None, base_url: str = ""):
        super().__init__(driver, base_url)
        self.current_settings: Dict[str, Any] = {}
        self.settings_endpoint = "/api/v1/settings"

        # Register settings elements
        self._register_settings_elements()

    def _register_settings_elements(self):
        """Register elements for settings page."""
        self.register_element(UIElement(
            name="language_selector",
            locator_type="css",
            locator_value="select[name='language'], #language-select",
            description="Language selection dropdown",
            is_critical=True
        ))
        self.register_element(UIElement(
            name="theme_toggle",
            locator_type="css",
            locator_value="toggle[name='theme'], #theme-toggle",
            description="Theme toggle switch",
            is_critical=False
        ))
        self.register_element(UIElement(
            name="notification_settings",
            locator_type="css",
            locator_value="#notifications, .notification-settings",
            description="Notification settings section",
            is_critical=False
        ))
        self.register_element(UIElement(
            name="save_button",
            locator_type="css",
            locator_value="button[type='submit'], #save-settings",
            description="Save settings button",
            is_critical=True
        ))
        self.register_element(UIElement(
            name="reset_button",
            locator_type="css",
            locator_value="button[class*='reset'], #reset-settings",
            description="Reset settings button",
            is_critical=False
        ))

    def wait_for_page_load(self, timeout: int = 30) -> bool:
        """Wait for settings page to load."""
        self._page_load_time = datetime.now()
        return True

    def is_page_loaded(self) -> bool:
        """Check if settings page is loaded."""
        return self._page_load_time is not None

    def get_current_settings(self, client: Any = None) -> Dict[str, Any]:
        """
        Get current chatbot settings.

        Args:
            client: Optional ChatBotClient for API-based settings retrieval

        Returns:
            Dictionary of current settings
        """
        if client:
            try:
                import requests
                response = requests.get(
                    f"{client.base_url}{self.settings_endpoint}",
                    headers=client._get_headers(),
                    timeout=10
                )
                if response.status_code == 200:
                    self.current_settings = response.json()
            except Exception as e:
                print(f"Failed to fetch settings: {e}")

        return self.current_settings

    def update_setting(self, key: str, value: Any, client: Any = None) -> bool:
        """
        Update a specific setting.

        Args:
            key: Setting key
            value: New value
            client: Optional ChatBotClient for API-based updates

        Returns:
            True if update successful
        """
        self.current_settings[key] = value

        if client:
            try:
                import requests
                response = requests.patch(
                    f"{client.base_url}{self.settings_endpoint}",
                    json={key: value},
                    headers=client._get_headers(),
                    timeout=10
                )
                return response.status_code in [200, 201]
            except Exception:
                return False

        return True

    def update_language(self, language: str, client: Any = None) -> bool:
        """
        Update chatbot language setting.

        Args:
            language: Language code (e.g., "en-US", "es-ES")
            client: Optional ChatBotClient

        Returns:
            True if update successful
        """
        return self.update_setting("language", language, client)

    def update_theme(self, theme: str, client: Any = None) -> bool:
        """
        Update chatbot theme setting.

        Args:
            theme: Theme name (e.g., "light", "dark", "auto")
            client: Optional ChatBotClient

        Returns:
            True if update successful
        """
        return self.update_setting("theme", theme, client)

    def reset_to_defaults(self, client: Any = None) -> bool:
        """
        Reset all settings to default values.

        Args:
            client: Optional ChatBotClient

        Returns:
            True if reset successful
        """
        default_settings = {
            "language": "en-US",
            "theme": "auto",
            "notifications": True,
            "sound_enabled": True
        }

        self.current_settings = default_settings.copy()

        if client:
            try:
                import requests
                response = requests.post(
                    f"{client.base_url}{self.settings_endpoint}/reset",
                    headers=client._get_headers(),
                    timeout=10
                )
                return response.status_code == 200
            except Exception:
                return False

        return True

    def validate_setting(self, key: str, expected_value: Any) -> bool:
        """
        Validate a setting has the expected value.

        Args:
            key: Setting key
            expected_value: Expected value

        Returns:
            True if setting matches expected
        """
        return self.current_settings.get(key) == expected_value

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return [
            "en-US", "en-GB", "es-ES", "es-MX", "fr-FR", "de-DE",
            "it-IT", "pt-BR", "ru-RU", "ar-SA", "zh-CN", "zh-TW",
            "ja-JP", "ko-KR", "hi-IN", "th-TH", "vi-VN"
        ]