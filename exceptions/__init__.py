"""
Custom exceptions for ChatBot Tester Framework.
Provides meaningful error types for different failure scenarios.
"""


class ChatBotTesterException(Exception):
    """Base exception for all ChatBot Tester framework errors."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(ChatBotTesterException):
    """Raised when authentication fails or is invalid."""
    def __init__(self, message: str = "Authentication failed", auth_type: str = None, details: dict = None):
        super().__init__(message, details)
        self.auth_type = auth_type


class ConfigurationError(ChatBotTesterException):
    """Raised when configuration is invalid or missing required fields."""
    pass


class ResponseTimeoutError(ChatBotTesterException):
    """Raised when chatbot response exceeds timeout threshold."""
    def __init__(self, message: str = "Response timeout exceeded", timeout: int = None,
                 actual_duration: float = None, details: dict = None):
        super().__init__(message, details)
        self.timeout = timeout
        self.actual_duration = actual_duration


class InvalidResponseError(ChatBotTesterException):
    """Raised when chatbot returns an invalid or unexpected response."""
    def __init__(self, message: str = "Invalid response received", status_code: int = None,
                 response_body: str = None, details: dict = None):
        super().__init__(message, details)
        self.status_code = status_code
        self.response_body = response_body


class RateLimitError(ChatBotTesterException):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None,
                 limit: int = None, details: dict = None):
        super().__init__(message, details)
        self.retry_after = retry_after
        self.limit = limit


class BiasDetectionError(ChatBotTesterException):
    """Raised when bias is detected in chatbot responses."""
    def __init__(self, message: str = "Bias detected", category: str = None,
                 severity: str = None, evidence: str = None, details: dict = None):
        super().__init__(message, details)
        self.category = category
        self.severity = severity
        self.evidence = evidence


class ConversationError(ChatBotTesterException):
    """Raised when conversation handling fails."""
    def __init__(self, message: str = "Conversation error", context_id: str = None,
                 message_index: int = None, details: dict = None):
        super().__init__(message, details)
        self.context_id = context_id
        self.message_index = message_index


class HealthCheckError(ChatBotTesterException):
    """Raised when chatbot health check fails."""
    def __init__(self, message: str = "Health check failed", endpoint: str = None,
                 status_code: int = None, response_time: float = None, details: dict = None):
        super().__init__(message, details)
        self.endpoint = endpoint
        self.status_code = status_code
        self.response_time = response_time


class ValidationError(ChatBotTesterException):
    """Raised when input validation fails."""
    def __init__(self, message: str = "Validation failed", field: str = None,
                 value: any = None, constraint: str = None, details: dict = None):
        super().__init__(message, details)
        self.field = field
        self.value = value
        self.constraint = constraint


class FlakyTestError(ChatBotTesterException):
    """Raised when a test fails due to flakiness after max retries."""
    def __init__(self, message: str = "Test failed after maximum retries",
                 test_name: str = None, attempts: int = None, last_error: str = None,
                 details: dict = None):
        super().__init__(message, details)
        self.test_name = test_name
        self.attempts = attempts
        self.last_error = last_error


class LocalizationError(ChatBotTesterException):
    """Raised when localization testing fails."""
    def __init__(self, message: str = "Localization error", locale: str = None,
                 missing_key: str = None, details: dict = None):
        super().__init__(message, details)
        self.locale = locale
        self.missing_key = missing_key


class SecurityError(ChatBotTesterException):
    """Raised when a security vulnerability is detected."""
    def __init__(self, message: str = "Security vulnerability detected",
                 vulnerability_type: str = None, severity: str = None,
                 payload: str = None, response_snippet: str = None, details: dict = None):
        super().__init__(message, details)
        self.vulnerability_type = vulnerability_type
        self.severity = severity
        self.payload = payload
        self.response_snippet = response_snippet


class ConnectionError(ChatBotTesterException):
    """Raised when connection to chatbot fails."""
    def __init__(self, message: str = "Connection failed", host: str = None,
                 port: int = None, reason: str = None, details: dict = None):
        super().__init__(message, details)
        self.host = host
        self.port = port
        self.reason = reason