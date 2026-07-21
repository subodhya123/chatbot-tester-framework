"""
Reusable helper functions for ChatBot testing.
Provides common utility functions for test automation.
"""

import time
import json
import yaml
import hashlib
import re
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
from contextlib import contextmanager


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator that retries a function on failure.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff

            raise last_exception

        return wrapper
    return decorator


def retry_flaky_test(max_attempts: int = 3, delay: float = 0.5):
    """
    Decorator specifically for flaky tests with automatic retry.
    Marks test as flaky if it fails after all retries.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        Decorated test function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)

            # If all retries failed, raise with context
            from exceptions import FlakyTestError
            raise FlakyTestError(
                message=f"Test failed after {max_attempts} attempts",
                test_name=func.__name__,
                attempts=max_attempts,
                last_error=str(last_error)
            )

        return wrapper
    return decorator


@contextmanager
def timer(description: str = "Operation"):
    """
    Context manager to time operations.

    Args:
        description: Description of the operation being timed

    Usage:
        with timer("API call"):
            result = api.call()
    """
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        print(f"[TIMER] {description}: {elapsed:.3f}s")


def wait_for_condition(
    condition: Callable[[], bool],
    timeout: float = 30.0,
    interval: float = 0.5,
    error_message: str = "Condition not met within timeout"
) -> bool:
    """
    Wait for a condition to become true.

    Args:
        condition: Callable that returns bool
        timeout: Maximum wait time in seconds
        interval: Time between checks in seconds
        error_message: Error message if timeout occurs

    Returns:
        True if condition met, raises TimeoutError otherwise
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition():
            return True
        time.sleep(interval)

    raise TimeoutError(error_message)


def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """
    Calculate exponential backoff delay.

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Calculated delay in seconds
    """
    delay = base_delay * (2 ** attempt)
    return min(delay, max_delay)


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load JSON data from a file.

    Args:
        file_path: Path to JSON file

    Returns:
        Dictionary containing JSON data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """
    Load YAML data from a file.

    Args:
        file_path: Path to YAML file

    Returns:
        Dictionary containing YAML data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_json_file(data: Dict[str, Any], file_path: str, indent: int = 2):
    """
    Save data to a JSON file.

    Args:
        data: Dictionary to save
        file_path: Path to output file
        indent: JSON indentation level
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def save_yaml_file(data: Dict[str, Any], file_path: str):
    """
    Save data to a YAML file.

    Args:
        data: Dictionary to save
        file_path: Path to output file
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False)


def generate_test_id(prefix: str = "test") -> str:
    """
    Generate a unique test ID.

    Args:
        prefix: Prefix for the test ID

    Returns:
        Unique test ID string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    hash_input = f"{prefix}_{timestamp}"
    hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    return f"{prefix}_{hash_value}"


def sanitize_string(text: str, max_length: int = None) -> str:
    """
    Sanitize a string for safe display/storage.

    Args:
        text: Input text
        max_length: Optional maximum length

    Returns:
        Sanitized string
    """
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

    # Trim whitespace
    text = text.strip()

    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length] + "..."

    return text


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.

    Args:
        text: Input text

    Returns:
        List of URLs found in text
    """
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(url_pattern, text)


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text.

    Args:
        text: Input text

    Returns:
        List of email addresses found
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)


def mask_sensitive_data(text: str) -> str:
    """
    Mask sensitive data patterns in text.

    Args:
        text: Input text

    Returns:
        Text with sensitive data masked
    """
    # Mask email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)

    # Mask phone numbers
    phone_pattern = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
    text = re.sub(phone_pattern, '[PHONE]', text)

    # Mask API keys (common patterns)
    api_key_pattern = r'[A-Za-z0-9]{20,}'
    text = re.sub(api_key_pattern, '[API_KEY]', text)

    return text


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using Jaccard index.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score between 0.0 and 1.0
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add when truncating

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 0.001:
        return f"{seconds * 1000000:.0f}μs"
    elif seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def parse_duration(duration_str: str) -> float:
    """
    Parse duration string to seconds.

    Args:
        duration_str: Duration string (e.g., "5s", "2m", "1h")

    Returns:
        Duration in seconds
    """
    units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }

    if not duration_str:
        return 0.0

    value = float(duration_str[:-1])
    unit = duration_str[-1]

    return value * units.get(unit, 1)


def merge_dicts(*dicts: Dict) -> Dict:
    """
    Merge multiple dictionaries, with later dicts overriding earlier ones.

    Args:
        *dicts: Dictionaries to merge

    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """
    Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator between keys

    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))

    return dict(items)


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Split a list into chunks of specified size.

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def get_nested_value(d: Dict, path: str, default: Any = None) -> Any:
    """
    Get a nested value from a dictionary using dot notation.

    Args:
        d: Dictionary
        path: Path to value (e.g., "a.b.c")
        default: Default value if path not found

    Returns:
        Value at path or default
    """
    keys = path.split('.')
    value = d

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default

    return value


def set_nested_value(d: Dict, path: str, value: Any):
    """
    Set a nested value in a dictionary using dot notation.

    Args:
        d: Dictionary
        path: Path to value (e.g., "a.b.c")
        value: Value to set
    """
    keys = path.split('.')
    current = d

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value


class TestDataGenerator:
    """Generate test data for various scenarios."""

    @staticmethod
    def generate_conversation_flow(num_turns: int = 5) -> List[str]:
        """Generate a basic conversation flow."""
        user_messages = [
            "Hello",
            "How are you?",
            "What can you help me with?",
            "Tell me more",
            "Thanks"
        ]
        return user_messages[:num_turns]

    @staticmethod
    def generate_long_message(length: int = 1000) -> str:
        """Generate a long message of specified length."""
        base_text = "This is a test message. "
        repeats = (length // len(base_text)) + 1
        return (base_text * repeats)[:length]

    @staticmethod
    def generate_unicode_message() -> str:
        """Generate a message with various unicode characters."""
        return "Hello! 🌍 你好 👋 مرحبا 🎉"

    @staticmethod
    def generate_special_chars_message() -> str:
        """Generate a message with special characters."""
        return "!@#$%^&*()_+-=[]{}|;':\",./<>?\\`~"


class ResponseValidator:
    """Validate chatbot responses against expected criteria."""

    @staticmethod
    def validate_not_empty(response: str) -> bool:
        """Check response is not empty."""
        return bool(response and response.strip())

    @staticmethod
    def validate_contains_keywords(response: str, keywords: List[str]) -> bool:
        """Check response contains expected keywords."""
        response_lower = response.lower()
        return any(kw.lower() in response_lower for kw in keywords)

    @staticmethod
    def validate_length(response: str, min_len: int = 0, max_len: int = None) -> bool:
        """Check response length is within bounds."""
        if len(response) < min_len:
            return False
        if max_len and len(response) > max_len:
            return False
        return True

    @staticmethod
    def validate_no_error_keywords(response: str) -> bool:
        """Check response doesn't contain error indicators."""
        error_keywords = ["error", "exception", "failed", "sorry"]
        response_lower = response.lower()
        return not any(kw in response_lower for kw in error_keywords)


class ConfigLoader:
    """Load and manage test configuration."""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from file."""
        if self._config is None:
            if config_path is None:
                config_path = Path(__file__).parent.parent / "config.yaml"

            self._config = load_yaml_file(str(config_path))

        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        if self._config is None:
            self.load()

        return get_nested_value(self._config, key, default)

    def reload(self, config_path: str = None):
        """Reload configuration from file."""
        self._config = None
        return self.load(config_path)


# Import Path for config loading
from pathlib import Path