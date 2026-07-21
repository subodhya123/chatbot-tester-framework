# ChatBot Tester Framework

A comprehensive, enterprise-ready testing framework for AI chatbots with built-in support for:

- **Multilingual/Localization Testing** - Test chatbots in 30+ languages including RTL support
- **Multiple Authentication Methods** - API keys, Bearer tokens, OAuth2, Basic Auth, Custom headers
- **LangTest Bias Checking** - Deep bias and fairness testing across demographic categories
- **Page Object Model (POM)** - Structured, maintainable test architecture
- **Flaky Test Handling** - Automatic retry with configurable attempts and delays
- **Comprehensive Test Suite** - Functional, performance, security, bias, and localization tests
- **Pytest HTML Reports** - Beautiful, shareable test reports with pytest-html

## Features

| Feature | Description |
|---------|-------------|
| **Localization** | Support for 30+ locales including Arabic, Hebrew (RTL), Chinese, Japanese, etc. |
| **POM Pattern** | BasePage, ChatPage, HealthPage, SettingsPage - reusable and maintainable |
| **Error Handling** | Custom exceptions for AuthenticationError, ResponseTimeoutError, BiasDetectionError, etc. |
| **Flaky Tests** | `@pytest.mark.flaky` - auto-retries with exponential backoff |
| **Retry Logic** | Configurable max retries, delay, and backoff multiplier |
| **Helper Functions** | retry_on_failure, timer, wait_for_condition, sanitize_string, etc. |

## Quick Start

### 1. Installation

```bash
pip install pytest pytest-html pytest-timeout requests pyyaml python-dotenv langtest
```

Or install from requirements:
```bash
cd chatbot_tester && pip install -r requirements.txt
```

### 2. Configure Your Chatbot

Edit `config.yaml`:

```yaml
chatbot:
  base_url: "http://localhost:8000"
  endpoints:
    chat: "/api/v1/chat"
    health: "/api/v1/health"

authentication:
  type: "bearer_token"  # Options: api_key, bearer_token, oauth2, basic_auth, custom_headers, none

bias_testing:
  enabled: true
  categories:
    - "gender"
    - "ethnicity"
    - "religion"

performance:
  thresholds:
    p50: 500
    p95: 1000
    p99: 2000
```

### 3. Set Environment Variables

```bash
export CHATBOT_BEARER_TOKEN="your-token-here"
# or for API key:
export CHATBOT_API_KEY="your-api-key"
```

### 4. Run Tests

```bash
# Run all tests with HTML report
pytest --html=reports/report.html --self-contained-html

# Run specific test types
pytest -m functional
pytest -m performance
pytest -m security
pytest -m bias
pytest -m localization

# Run with custom chatbot name
pytest --chatbot-name="My ChatBot" --html=reports/report.html
```

## Project Structure

```
chatbot_tester/
├── auth/                      # Authentication strategies
│   └── __init__.py
├── clients/                   # ChatBot client implementations
│   └── __init__.py
├── conftest.py                # Pytest configuration, fixtures, flaky test handling
├── config.yaml                # All configurable parameters
├── exceptions/                 # Custom exception classes
│   └── __init__.py
├── fixtures/                  # Reusable test fixtures
│   └── __init__.py
├── helpers/                   # Utility functions
│   └── __init__.py
├── locales/                   # Localization data files
│   ├── en-US.json
│   ├── es-ES.json
│   ├── fr-FR.json
│   └── ... (30+ locales)
├── pom/                       # Page Object Model structure
│   ├── __init__.py
│   └── pages/
│       ├── base_page.py       # BasePageObject abstract class
│       ├── chat_page.py       # ChatPage POM
│       ├── health_page.py     # HealthPage POM
│       └── settings_page.py  # SettingsPage POM
├── plugins/                   # Custom pytest plugins
│   └── __init__.py
├── reports/                   # Test reports output
├── tests/                     # Test suites
│   ├── test_bias.py
│   ├── test_functional.py
│   ├── test_integration.py
│   ├── test_localization.py   # Localization tests
│   ├── test_performance.py
│   └── test_security.py
└── utils/
    └── __init__.py
```

## Authentication Types

| Type | Environment Variable | Description |
|------|---------------------|-------------|
| `none` | - | No authentication (public chatbots) |
| `api_key` | `CHATBOT_API_KEY` | API key in custom header |
| `bearer_token` | `CHATBOT_BEARER_TOKEN` | Bearer token authentication |
| `basic_auth` | `CHATBOT_USERNAME`, `CHATBOT_PASSWORD` | HTTP Basic Auth |
| `oauth2` | `CHATBOT_CLIENT_ID`, `CHATBOT_CLIENT_SECRET` | OAuth2 client credentials |
| `custom_headers` | Set in config.yaml | Custom header pairs |

## Localization Support

### Supported Locales

The framework supports 30+ locales including:

- **English**: en-US, en-GB
- **European**: es-ES, es-MX, fr-FR, de-DE, it-IT, pt-BR, ru-RU, uk-UA
- **RTL Languages**: ar-SA (Arabic), he-IL (Hebrew), fa-IR (Persian), ur-PK (Urdu)
- **Asian**: zh-CN, zh-TW, ja-JP, ko-KR, hi-IN, th-TH, vi-VN, id-ID, ms-MY
- **Others**: tr-TR, pl-PL, nl-NL, sv-SE, da-DK, no-NO, fi-FI, el-GR, cs-CZ, hu-HU, ro-RO

### Using Localization in Tests

```python
# Using localization manager directly
from locales import LocalizationManager

loc_manager = LocalizationManager()
greeting = loc_manager.get_greeting("es-ES")  # Returns "Hola"
question = loc_manager.get_question("fr-FR", "how_are_you")  # Returns "Comment allez-vous?"

# Using POM with localization
from pom.pages import ChatPage

chat_page = ChatPage(base_url="http://localhost:8000")
conversation = chat_page.create_localized_conversation("ar-SA")  # Arabic RTL

response = chat_page.send_locale_aware_message(
    message_key="hello",
    category="greetings",
    client=chatbot_client,
    locale="es-ES"
)
```

### Running Localization Tests

```bash
# Test specific locales
pytest -m localization --test-locales="en-US,es-ES,fr-FR"

# Test with default locale
pytest -m localization --locale="es-ES"

# Test RTL languages
pytest -m localization --test-locales="ar-SA,he-IL"
```

## Page Object Model (POM)

### Available Page Objects

```python
from pom.pages import ChatPage, HealthPage, SettingsPage, create_page_object

# Direct instantiation
chat_page = ChatPage(base_url="http://localhost:8000")
health_page = HealthPage(base_url="http://localhost:8000")

# Factory method
chat_page = create_page_object("chat", base_url="http://localhost:8000")

# Create all pages at once
from pom import create_all_pages
pages = create_all_pages(base_url="http://localhost:8000")
pages["chat"]  # ChatPage instance
pages["health"]  # HealthPage instance
```

### Using ChatPage POM

```python
# Create chat page
chat_page = ChatPage(base_url="http://localhost:8000")

# Create conversation context
conversation = chat_page.create_conversation()

# Send messages
response = chat_page.send_message("Hello!", client=chatbot_client)

# Send localized messages
response = chat_page.send_locale_aware_message(
    message_key="hello",
    category="greetings",
    client=chatbot_client,
    locale="es-ES"
)

# Validate responses
validation = chat_page.validate_response_content(
    response,
    expected_keywords=["hello", "hi"],
    min_length=5,
    max_length=500
)
assert validation["is_valid"], validation["errors"]

# Get conversation statistics
stats = chat_page.get_conversation_stats()
print(f"Messages: {stats['message_count']}, Avg response: {stats['avg_response_time_ms']}ms")
```

## Flaky Test Handling

### Marking Tests as Flaky

```python
import pytest

@pytest.mark.flaky
def test_sometimes_fails():
    """This test will auto-retry on failure."""
    # Test code here
    pass

@pytest.mark.flaky(max_retries=5, delay=2.0)
def test_with_custom_retries():
    """Flaky test with custom retry configuration."""
    # Test code here
    pass

@pytest.mark.retry
def test_always_retries():
    """Test that always retries on failure."""
    # Test code here
    pass
```

### Command Line Options for Flaky Tests

```bash
# Default: 3 retries with 1.0s delay
pytest --max-retries=3 --retry-delay=1.0

# More aggressive retry
pytest --max-retries=5 --retry-delay=0.5

# No retry (for debugging)
pytest --max-retries=1
```

### Using Retry Decorator in Test Code

```python
from helpers import retry_on_failure, retry_flaky_test

# Decorator for any function
@retry_on_failure(max_attempts=3, delay=1.0, backoff=2.0)
def call_chatbot_with_retry(message):
    # Function with automatic retry on failure
    return chatbot_client.send_message(message)

# Direct flaky test decorator
@retry_flaky_test(max_attempts=3, delay=0.5)
def test_flaky_endpoint():
    # Test function that will auto-retry
    pass
```

## Error Handling

### Custom Exceptions

```python
from exceptions import (
    ChatBotTesterException,
    AuthenticationError,
    ResponseTimeoutError,
    InvalidResponseError,
    RateLimitError,
    BiasDetectionError,
    FlakyTestError,
    LocalizationError,
    SecurityError
)

# Using exceptions in tests
def test_something():
    try:
        response = chatbot_client.send_message("test")
    except ResponseTimeoutError as e:
        print(f"Response took too long: {e.actual_duration}ms (limit: {e.timeout}ms)")
    except BiasDetectionError as e:
        print(f"Bias detected in category {e.category}: {e.evidence}")
```

### Error Handler Fixture

```python
def test_with_error_tracking(error_handler):
    # Capture errors during test
    try:
        response = chatbot_client.send_message("test")
    except Exception as e:
        error_handler.capture_error(e, {"test": "value"})

    # Check for errors
    if error_handler.has_errors():
        summary = error_handler.get_error_summary()
        print(f"Errors: {summary['error_count']}")
```

## Helper Functions

```python
from helpers import (
    retry_on_failure,
    timer,
    wait_for_condition,
    exponential_backoff,
    sanitize_string,
    extract_urls,
    mask_sensitive_data,
    calculate_text_similarity,
    format_duration,
    load_json_file,
    save_json_file,
    TestDataGenerator,
    ResponseValidator,
    ConfigLoader
)

# Timer context manager
with timer("API call"):
    result = api.call()

# Wait for condition
wait_for_condition(
    condition=lambda: is_healthy(),
    timeout=30.0,
    interval=0.5
)

# Sanitize sensitive data
safe_text = sanitize_string(raw_response, max_length=100)

# Validate response
is_valid = ResponseValidator.validate_contains_keywords(
    response,
    keywords=["hello", "hi"]
)

# Generate test data
long_msg = TestDataGenerator.generate_long_message(1000)
unicode_msg = TestDataGenerator.generate_unicode_message()
```

## Test Markers

| Marker | Description |
|--------|-------------|
| `@pytest.mark.functional` | Functional behavior tests |
| `@pytest.mark.performance` | Performance and load tests |
| `@pytest.mark.security` | Security vulnerability tests |
| `@pytest.mark.bias` | Bias detection tests |
| `@pytest.mark.localization` | Localization and multilingual tests |
| `@pytest.mark.integration` | Integration tests |
| `@pytest.mark.e2e` | End-to-end tests |
| `@pytest.mark.flaky` | Flaky tests with auto-retry |
| `@pytest.mark.slow` | Slow tests (skipped with `--skip-slow`) |

## Command Line Options

| Option | Description |
|--------|-------------|
| `--chatbot-name` | Name for HTML report title |
| `--baseline-file` | Path to baseline for regression |
| `--skip-slow` | Skip slow running tests |
| `--auth-type` | Override authentication type |
| `--max-retries` | Max retry attempts for flaky tests (default: 3) |
| `--retry-delay` | Delay between retry attempts (default: 1.0s) |
| `--locale` | Default locale (default: en-US) |
| `--test-locales` | Comma-separated locales to test |
| `--html` | HTML report output path |
| `--self-contained-html` | Make HTML report self-contained |

## CI/CD Integration

### GitHub Actions Example

```yaml
name: ChatBot Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r chatbot_tester/requirements.txt

      - name: Run tests
        env:
          CHATBOT_BEARER_TOKEN: ${{ secrets.CHATBOT_TOKEN }}
        run: |
          cd chatbot_tester
          pytest --html=reports/report.html --self-contained-html -m "not slow"

      - name: Upload reports
        uses: actions/upload-artifact@v4
        with:
          name: test-reports
          path: chatbot_tester/reports/
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any

    stages {
        stage('Test') {
            steps {
                sh '''
                    cd chatbot_tester
                    pytest --html=reports/report.html \
                           --self-contained-html \
                           --chatbot-name="${CHATBOT_NAME}" \
                           -m "functional and not slow"
                '''
            }
        }

        stage('Publish Reports') {
            steps {
                publishHTML([allowMissing: false,
                             alwaysLinkToLastBuild: true,
                             keepAll: true,
                             reportDir: 'chatbot_tester/reports',
                             reportFiles: 'report.html',
                             reportName: 'ChatBot Test Report'])
            }
        }
    }
}
```

## Writing Tests

### Basic Functional Test

```python
import pytest
from clients import ChatBotClient
from pom.pages import ChatPage

@pytest.mark.functional
def test_greeting(chatbot_client):
    """Test chatbot responds to greeting."""
    response = chatbot_client.send_message("Hello!")
    assert response.success
    assert len(response.message.content) > 0

@pytest.mark.functional
def test_conversation_with_pom():
    """Test using POM pattern."""
    chat_page = ChatPage(base_url="http://localhost:8000")
    conversation = chat_page.create_conversation()

    response = chat_page.send_message(
        "My favorite color is blue",
        client=chatbot_client,
        conversation=conversation
    )

    # Follow-up question
    response2 = chat_page.send_message(
        "What's my favorite color?",
        client=chatbot_client,
        conversation=conversation
    )

    assert "blue" in response2.message.content.lower()
```

### Localization Test

```python
@pytest.mark.localization
@pytest.mark.parametrize("locale", ["en-US", "es-ES", "fr-FR"])
def test_greeting_in_locale(chatbot_client, localization_manager, locale):
    """Test chatbot responds to localized greetings."""
    greeting = localization_manager.get_greeting(locale)
    response = chatbot_client.send_message(greeting)

    assert response.success
    assert len(response.message.content) > 0
```

### Flaky Test with POM

```python
@pytest.mark.flaky
@pytest.mark.e2e
def test_conversation_flow_with_retry(chatbot_client):
    """End-to-end conversation that may be flaky."""
    chat_page = ChatPage(base_url="http://localhost:8000")

    responses = chat_page.send_locale_flow(
        flow_name="greeting",
        client=chatbot_client,
        locale="en-US"
    )

    for response in responses:
        assert response.success, f"Failed: {response.error}"
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CHATBOT_API_KEY` | API key for authentication |
| `CHATBOT_BEARER_TOKEN` | Bearer token |
| `CHATBOT_USERNAME` | Username for basic auth |
| `CHATBOT_PASSWORD` | Password for basic auth |
| `CHATBOT_CLIENT_ID` | OAuth2 client ID |
| `CHATBOT_CLIENT_SECRET` | OAuth2 client secret |
| `CHATBOT_CUSTOM_AUTH` | Custom header value |
| `CHATBOT_OAUTH_SCOPE` | OAuth2 scope (space-separated) |
| `CHATBOT_TEST_CONFIG` | Override config file path |
| `CHATBOT_BASE_URL` | Override chatbot base URL |

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.