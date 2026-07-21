"""
Health Check Page Object - POM for chatbot health and status endpoints.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pom.pages.base_page import BasePageObject, UIElement
from clients import ChatBotClient


class HealthPage(BasePageObject):
    """
    Page Object for chatbot health check and status monitoring.
    Provides methods for checking chatbot availability and status.
    """

    def __init__(self, driver: Any = None, base_url: str = "", health_endpoint: str = "/api/v1/health"):
        super().__init__(driver, base_url)
        self.health_endpoint = health_endpoint
        self.last_check_time: Optional[datetime] = None
        self.last_check_result: Optional[Dict[str, Any]] = None

        # Register health page elements
        self._register_health_elements()

    def _register_health_elements(self):
        """Register elements for health check page."""
        self.register_element(UIElement(
            name="status_indicator",
            locator_type="css",
            locator_value=".health-status, #health-indicator",
            description="Health status indicator",
            is_critical=True
        ))
        self.register_element(UIElement(
            name="version_info",
            locator_type="css",
            locator_value=".version, #api-version",
            description="API version information",
            is_critical=False
        ))
        self.register_element(UIElement(
            name="uptime_display",
            locator_type="css",
            locator_value=".uptime, #uptime",
            description="System uptime display",
            is_critical=False
        ))

    def wait_for_page_load(self, timeout: int = 30) -> bool:
        """Wait for health page to be accessible."""
        self._page_load_time = datetime.now()
        return True

    def is_page_loaded(self) -> bool:
        """Check if health page is accessible."""
        return self._page_load_time is not None

    def check_health(self, client: ChatBotClient) -> Dict[str, Any]:
        """
        Perform a health check on the chatbot.

        Args:
            client: ChatBotClient instance

        Returns:
            Health check results dictionary
        """
        self.last_check_time = datetime.now()

        health_result = client.health_check()
        self.last_check_result = health_result

        return self._format_health_result(health_result)

    def _format_health_result(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format raw health result into structured format."""
        formatted = {
            "healthy": raw_result.get("healthy", False),
            "timestamp": self.last_check_time.isoformat() if self.last_check_time else None,
            "response_time_ms": None,
            "status_code": None,
            "error_message": None,
            "details": {}
        }

        if "status_code" in raw_result:
            formatted["status_code"] = raw_result["status_code"]

        if "response" in raw_result:
            response_data = raw_result["response"]
            if isinstance(response_data, dict):
                formatted["details"] = response_data
                if "version" in response_data:
                    formatted["details"]["version"] = response_data["version"]
                if "uptime" in response_data:
                    formatted["details"]["uptime"] = response_data["uptime"]

        if "error" in raw_result:
            formatted["error_message"] = raw_result["error"]

        return formatted

    def is_healthy(self, client: ChatBotClient) -> bool:
        """
        Quick check if chatbot is healthy.

        Args:
            client: ChatBotClient instance

        Returns:
            True if healthy, False otherwise
        """
        health = client.health_check()
        return health.get("healthy", False)

    def wait_until_healthy(self, client: ChatBotClient, timeout: int = 60, interval: float = 5.0) -> bool:
        """
        Wait until chatbot becomes healthy.

        Args:
            client: ChatBotClient instance
            timeout: Maximum wait time in seconds
            interval: Time between checks in seconds

        Returns:
            True if chatbot became healthy, False if timeout
        """
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.is_healthy(client):
                return True
            time.sleep(interval)

        return False

    def get_status_summary(self, client: ChatBotClient) -> str:
        """
        Get a human-readable status summary.

        Args:
            client: ChatBotClient instance

        Returns:
            Status summary string
        """
        health = self.check_health(client)

        if health["healthy"]:
            summary = "✅ ChatBot is healthy"
            if health.get("status_code"):
                summary += f" (Status: {health['status_code']})"
        else:
            summary = f"❌ ChatBot is unhealthy"
            if health.get("error_message"):
                summary += f" - {health['error_message']}"

        return summary

    def record_health_metrics(self) -> Dict[str, Any]:
        """
        Record health metrics for monitoring.

        Returns:
            Metrics dictionary
        """
        if not self.last_check_result:
            return {"error": "No health check performed yet"}

        return {
            "timestamp": self.last_check_time.isoformat() if self.last_check_time else None,
            "healthy": self.last_check_result.get("healthy", False),
            "response_time": self.last_check_result.get("response_time", 0),
            "status_code": self.last_check_result.get("status_code")
        }