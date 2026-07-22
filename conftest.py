"""
Enhanced Pytest configuration with flaky test handling, error handling, and localization support.
"""

import pytest
import yaml
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from clients import ChatBotClient, ChatBotClientBuilder, ConversationContext
from auth import AuthFactory, NoAuth
from locales import LocalizationManager, get_localization_manager, LocalizedConversationContext
from exceptions import (
    ChatBotTesterException,
    FlakyTestError,
    ResponseTimeoutError,
    AuthenticationError,
    InvalidResponseError
)


# ============================================================================
# FLaky Test Configuration
# ============================================================================

def pytest_addoption(parser):
    """Add custom command line options for flaky test handling."""
    parser.addoption(
        "--chatbot-name",
        action="store",
        default="ChatBot",
        help="Name of the chatbot being tested"
    )
    parser.addoption(
        "--baseline-file",
        action="store",
        default=None,
        help="Path to baseline performance file for regression testing"
    )
    parser.addoption(
        "--skip-slow",
        action="store_true",
        default=False,
        help="Skip slow running tests"
    )
    parser.addoption(
        "--auth-type",
        action="store",
        default=None,
        help="Override authentication type from config"
    )
    parser.addoption(
        "--max-retries",
        action="store",
        type=int,
        default=3,
        help="Maximum retry attempts for flaky tests"
    )
    parser.addoption(
        "--retry-delay",
        action="store",
        type=float,
        default=1.0,
        help="Delay between retry attempts in seconds"
    )
    parser.addoption(
        "--locale",
        action="store",
        default="en-US",
        help="Default locale for localization tests"
    )
    parser.addoption(
        "--test-locales",
        action="store",
        default="en-US,es-ES,fr-FR,de-DE,zh-CN,ar-SA",
        help="Comma-separated list of locales to test"
    )


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    # Register standard markers
    config.addinivalue_line("markers", "bias: mark test as a bias checking test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "security: mark test as a security test")
    config.addinivalue_line("markers", "functional: mark test as a functional test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "localization: mark test as a localization test")

    # Register flaky test markers
    config.addinivalue_line("markers", "flaky: mark test as flaky (will retry)")
    config.addinivalue_line("markers", "slow: mark test as slow (deselect with --skip-slow)")
    config.addinivalue_line("markers", "retry: mark test to always retry on failure")


# ============================================================================
# Session-scoped Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def config() -> Dict[str, Any]:
    """
    Load and provide configuration from config.yaml.
    Looks for config file in multiple locations.
    """
    possible_paths = [
        Path(__file__).parent.parent / "config.yaml",
        Path.cwd() / "config.yaml",
        Path.home() / ".chatbot_tester" / "config.yaml"
    ]

    config_path = None
    for path in possible_paths:
        if path.exists():
            config_path = path
            break

    # Allow override via environment variable
    config_env = os.getenv("CHATBOT_TEST_CONFIG")
    if config_env:
        config_path = Path(config_env)

    if not config_path or not config_path.exists():
        pytest.fail(f"Configuration file not found. Searched: {[str(p) for p in possible_paths]}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def chatbot_config(config) -> Dict[str, Any]:
    """
    Get chatbot-specific configuration.
    Returns the 'chatbot' section from config or defaults.
    """
    return config.get("chatbot", {
        "base_url": "http://localhost:8000",
        "endpoints": {
            "chat": "/api/v1/chat",
            "health": "/api/v1/health"
        },
        "timeout": 30,
        "max_retries": 3
    })


@pytest.fixture(scope="session")
def auth_config(config) -> Dict[str, Any]:
    """
    Get authentication configuration.
    Returns the 'authentication' section from config.
    """
    return config.get("authentication", {"type": "none"})


@pytest.fixture(scope="session")
def localization_manager(config) -> LocalizationManager:
    """
    Provide the localization manager for multilingual testing.
    Loads locale data from the locales directory.
    """
    locales_dir = Path(__file__).parent.parent / "locales"
    return get_localization_manager(str(locales_dir))


@pytest.fixture(scope="session")
def supported_locales(request) -> list:
    """
    Get list of locales to test based on command line option.
    Default: en-US,es-ES,fr-FR,de-DE,zh-CN,ar-SA
    """
    locales_str = request.config.getoption("--test-locales")
    return [loc.strip() for loc in locales_str.split(",")]


# ============================================================================
# Authentication Fixture with Error Handling
# ============================================================================

@pytest.fixture
def auth_strategy(auth_config, request) -> Any:
    """
    Create and validate authentication strategy based on config.

    Raises:
        AuthenticationError: If auth configuration is invalid
    """
    auth_type = auth_config.get("type", "none")

    # Allow override via command line
    cli_auth_type = request.config.getoption("--auth-type")
    if cli_auth_type:
        auth_type = cli_auth_type

    # Build auth parameters based on type
    auth_params = {}
    if auth_type == "api_key":
        auth_params["header_name"] = auth_config.get("api_key", {}).get(
            "header_name", "X-API-Key"
        )
    elif auth_type == "bearer_token":
        pass  # Uses environment variable CHATBOT_BEARER_TOKEN
    elif auth_type == "basic_auth":
        auth_params["username_env"] = auth_config.get("basic_auth", {}).get(
            "username_env", "CHATBOT_USERNAME"
        )
        auth_params["password_env"] = auth_config.get("basic_auth", {}).get(
            "password_env", "CHATBOT_PASSWORD"
        )
    elif auth_type == "oauth2":
        oauth_config = auth_config.get("oauth2", {})
        auth_params["token_url"] = oauth_config.get("token_url", "")
        auth_params["scope"] = oauth_config.get("scope", "chatbot:read chatbot:write")
    elif auth_type == "custom_headers":
        auth_params["headers"] = auth_config.get("custom_headers", {})

    try:
        strategy = AuthFactory.create(auth_type, **auth_params)

        # Validate authentication configuration
        valid, error = strategy.validate_config()
        if not valid:
            # Skip test if auth is not configured (not an error)
            if "not provided" in error.lower() or "not found" in error.lower():
                pytest.skip(f"Authentication not configured: {error}")
            raise AuthenticationError(error, auth_type=auth_type)

        return strategy

    except ValueError as e:
        # Unknown auth type - try to use no auth
        if "unknown auth type" in str(e).lower():
            return AuthFactory.create("none")
        raise AuthenticationError(str(e), auth_type=auth_type)


# ============================================================================
# ChatBot Client Fixture with Retry Logic
# ============================================================================

@pytest.fixture
def chatbot_client(chatbot_config, auth_strategy, request) -> ChatBotClient:
    """
    Create a configured ChatBotClient instance with retry handling.

    The client includes automatic retry on transient failures and
    proper error handling for various failure scenarios.
    """
    max_retries = request.config.getoption("--max-retries")

    # Build client using builder pattern
    builder = ChatBotClientBuilder()
    builder.set_base_url(chatbot_config.get("base_url", "http://localhost:8000"))

    # Map auth type to factory name
    auth_type_map = {
        "APIKeyAuth": "api_key",
        "BearerTokenAuth": "bearer_token",
        "BasicAuth": "basic_auth",
        "OAuth2Auth": "oauth2",
        "CustomHeadersAuth": "custom_headers",
        "NoAuth": "none"
    }

    auth_name = auth_type_map.get(auth_strategy.__class__.__name__, "none")
    builder.set_auth(auth_name)

    # Set timeouts and retries
    timeout = chatbot_config.get("timeout", 30)
    builder.set_timeout(timeout)

    configured_retries = chatbot_config.get("max_retries", 3)
    builder.set_max_retries(max(configured_retries, max_retries))

    return builder.build()


# ============================================================================
# Conversation Context Fixtures
# ============================================================================

@pytest.fixture
def conversation_context() -> ConversationContext:
    """
    Provide a fresh conversation context for each test.
    Automatically cleaned up after test completion.
    """
    return ConversationContext()


@pytest.fixture
def localized_conversation_context(localization_manager, request) -> 'LocalizedConversationContext':
    """
    Provide a fresh localized conversation context.

    Args:
        localization_manager: Injected localization manager
        request: Pytest request object for locale option

    Returns:
        LocalizedConversationContext instance
    """
    locale = request.config.getoption("--locale")
    return LocalizedConversationContext(locale=locale, localization_manager=localization_manager)


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def bias_config(config) -> Dict[str, Any]:
    """Get bias testing configuration from config.yaml."""
    return config.get("bias_testing", {"enabled": True, "categories": ["gender", "ethnicity"]})


@pytest.fixture
def performance_config(config) -> Dict[str, Any]:
    """Get performance testing configuration from config.yaml."""
    return config.get("performance", {
        "enabled": True,
        "thresholds": {"p50": 500, "p95": 1000, "p99": 2000}
    })


@pytest.fixture
def security_config(config) -> Dict[str, Any]:
    """Get security testing configuration from config.yaml."""
    return config.get("security", {
        "enabled": True,
        "check_sql_injection": True,
        "check_xss": True,
        "check_prompt_injection": True
    })


@pytest.fixture
def test_scenarios(config) -> list:
    """Get test scenarios from configuration."""
    return config.get("test_data", {}).get("scenarios", [])


@pytest.fixture
def reporting_config(config) -> Dict[str, Any]:
    """Get reporting configuration from config.yaml."""
    return config.get("reporting", {"output_dir": "./reports"})


# ============================================================================
# Flaky Test Handling
# ============================================================================

class FlakyTestTracker:
    """Track flaky test retries and failures."""

    def __init__(self):
        self.test_results: Dict[str, Dict] = {}
        self.flaky_tests: set = set()

    def record_attempt(self, test_name: str, passed: bool, error: str = None):
        """Record a test attempt result."""
        if test_name not in self.test_results:
            self.test_results[test_name] = {
                "attempts": 0,
                "passed": False,
                "errors": []
            }

        self.test_results[test_name]["attempts"] += 1
        if passed:
            self.test_results[test_name]["passed"] = True
        else:
            self.test_results[test_name]["errors"].append(error)

    def is_flaky(self, test_name: str) -> bool:
        """Check if a test is known to be flaky."""
        return test_name in self.flaky_tests

    def mark_flaky(self, test_name: str):
        """Mark a test as flaky."""
        self.flaky_tests.add(test_name)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about flaky tests."""
        return {
            "total_tracked": len(self.test_results),
            "flaky_count": len(self.flaky_tests),
            "details": self.test_results
        }


@pytest.fixture
def flaky_tracker() -> FlakyTestTracker:
    """Provide a tracker for flaky test monitoring."""
    return FlakyTestTracker()


# ============================================================================
# Pytest Hooks for Flaky Test Handling
# ============================================================================

def pytest_runtest_setup(item):
    """
    Called before each test execution.
    Handles flaky test retry configuration.
    """
    # Check if test is marked as flaky
    if item.get_closest_marker("flaky") or item.get_closest_marker("retry"):
        # Store original function for retry
        original_func = item.obj

        max_retries = item.config.getoption("--max-retries", 3)
        retry_delay = item.config.getoption("--retry-delay", 1.0)

        def retry_wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return original_func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        print(f"\n[RETRY] {item.name} attempt {attempt + 2}/{max_retries}")
            # All retries exhausted - raise original error
            raise last_error

        # Replace test function with wrapped version
        item.obj = retry_wrapper


def pytest_runtest_makereport(item, call):
    """
    Hook to capture test results and handle flaky test reporting.
    Called after test execution phase.
    """
    if call.when == "call":
        # Store rep_call on item for later access
        rep = call.excinfo

        if rep is None:
            # Test passed
            item._test_passed = True
        else:
            # Test failed
            item._test_passed = False
            item._test_error = str(rep.value if rep else None)

            # Check if test should be retried
            if item.get_closest_marker("flaky") or item.get_closest_marker("retry"):
                if hasattr(item.config, '_flaky_tracker'):
                    item.config._flaky_tracker.record_attempt(
                        item.name,
                        passed=False,
                        error=str(rep.value if rep else None)
                    )


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Add custom summary section for flaky tests.
    Called at the end of test run.
    """
    if hasattr(config, '_flaky_tracker'):
        tracker = config._flaky_tracker
        stats = tracker.get_stats()

        if stats["flaky_count"] > 0:
            terminalreporter.section("Flaky Test Summary")
            terminalreporter.write_line(f"Total tracked: {stats['total_tracked']}")
            terminalreporter.write_line(f"Flaky tests: {stats['flaky_count']}", yellow=True)

            for test_name in tracker.flaky_tests:
                details = stats["details"].get(test_name, {})
                terminalreporter.write_line(f"  - {test_name}: {details.get('attempts', 0)} attempts")


# ============================================================================
# Error Handling Hooks
# ============================================================================

def pytest_runtest_makereport(item, call):
    """
    Called after test execution phase to add extra info.
    Provides additional error context.
    """
    pass  # Placeholder - hooks managed elsewhere


@pytest.fixture
def error_handler():
    """
    Provide an error handler fixture for tests.
    Can be used to capture and analyze errors.
    """
    class ErrorHandler:
        def __init__(self):
            self.errors = []
            self.warnings = []

        def capture_error(self, error: Exception, context: Dict = None):
            """Capture an error with context."""
            self.errors.append({
                "error": str(error),
                "type": type(error).__name__,
                "context": context or {},
                "timestamp": time.time()
            })

        def capture_warning(self, message: str, context: Dict = None):
            """Capture a warning with context."""
            self.warnings.append({
                "message": message,
                "context": context or {},
                "timestamp": time.time()
            })

        def has_errors(self) -> bool:
            """Check if any errors have been captured."""
            return len(self.errors) > 0

        def get_error_summary(self) -> Dict[str, Any]:
            """Get a summary of captured errors."""
            return {
                "error_count": len(self.errors),
                "warning_count": len(self.warnings),
                "errors": self.errors,
                "warnings": self.warnings
            }

    return ErrorHandler()


# ============================================================================
# Localization Fixtures
# ============================================================================

@pytest.fixture
def default_locale(request) -> str:
    """Get the default locale for testing."""
    return request.config.getoption("--locale")


@pytest.fixture
def test_locales(request) -> list:
    """Get the list of locales to test."""
    locales_str = request.config.getoption("--test-locales")
    return [loc.strip() for loc in locales_str.split(",")]


@pytest.fixture
def localization_test_data(localization_manager) -> Dict[str, Any]:
    """
    Provide localized test data for testing.
    Returns phrases in multiple locales.
    """
    return {
        locale: {
            "greetings": localization_manager.get_translation(locale, "hello", "greetings"),
            "questions": localization_manager.get_translation(locale, "how_are_you", "questions"),
            "farewell": localization_manager.get_translation(locale, "goodbye", "greetings")
        }
        for locale in localization_manager.get_all_locales()
    }


# ============================================================================
# Test Isolation Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_between_tests():
    """
    Auto-use fixture to ensure test isolation.
    Runs before and after each test.
    """
    # Setup: nothing needed
    yield
    # Teardown: clean up any state
    pass


@pytest.fixture
def clean_conversation(chatbot_client):
    """
    Ensure a clean conversation state before test.
    Returns the client after reset.
    """
    chatbot_client.reset_session()
    return chatbot_client


# ============================================================================
# Performance Measurement Fixtures
# ============================================================================

@pytest.fixture
def measure_response_time():
    """
    Fixture to measure response time of an operation.
    Returns a context manager for timing.
    """
    class ResponseTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.elapsed_ms = 0

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, *args):
            self.end_time = time.time()
            self.elapsed_ms = (self.end_time - self.start_time) * 1000

        def get_elapsed_ms(self) -> float:
            return self.elapsed_ms

    return ResponseTimer()


# ============================================================================
# Custom Report Hooks
# ============================================================================

# Note: pytest-html hooks are registered differently
# Title customization is done via --chatbot-name option processed in conftest