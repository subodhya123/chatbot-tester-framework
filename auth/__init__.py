"""
Authentication module for ChatBot Tester Framework.
Supports multiple authentication methods for enterprise and open-source chatbots.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple
import os
import base64
from dataclasses import dataclass
import requests


@dataclass
class AuthResult:
    """Result of authentication attempt."""
    success: bool
    headers: Dict[str, str]
    error_message: Optional[str] = None


class AuthStrategy(ABC):
    """Abstract base class for authentication strategies."""

    @abstractmethod
    def authenticate(self) -> AuthResult:
        """Perform authentication and return headers."""
        pass

    @abstractmethod
    def validate_config(self) -> Tuple[bool, Optional[str]]:
        """Validate that required configuration is present."""
        pass


class APIKeyAuth(AuthStrategy):
    """API Key authentication strategy."""

    def __init__(self, api_key: Optional[str] = None, header_name: str = "X-API-Key"):
        self.api_key = api_key or os.getenv("CHATBOT_API_KEY")
        self.header_name = header_name

    def validate_config(self) -> Tuple[bool, Optional[str]]:
        if not self.api_key:
            return False, "API key not provided. Set CHATBOT_API_KEY environment variable."
        return True, None

    def authenticate(self) -> AuthResult:
        valid, error = self.validate_config()
        if not valid:
            return AuthResult(success=False, headers={}, error_message=error)

        return AuthResult(
            success=True,
            headers={self.header_name: self.api_key}
        )


class BearerTokenAuth(AuthStrategy):
    """Bearer token authentication strategy."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("CHATBOT_BEARER_TOKEN")

    def validate_config(self) -> Tuple[bool, Optional[str]]:
        if not self.token:
            return False, "Bearer token not provided. Set CHATBOT_BEARER_TOKEN environment variable."
        return True, None

    def authenticate(self) -> AuthResult:
        valid, error = self.validate_config()
        if not valid:
            return AuthResult(success=False, headers={}, error_message=error)

        return AuthResult(
            success=True,
            headers={"Authorization": f"Bearer {self.token}"}
        )


class BasicAuth(AuthStrategy):
    """Basic authentication strategy."""

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        username_env: str = "CHATBOT_USERNAME",
        password_env: str = "CHATBOT_PASSWORD"
    ):
        self.username = username or os.getenv(username_env)
        self.password = password or os.getenv(password_env)

    def validate_config(self) -> Tuple[bool, Optional[str]]:
        if not self.username or not self.password:
            return False, "Username or password not provided."
        return True, None

    def authenticate(self) -> AuthResult:
        valid, error = self.validate_config()
        if not valid:
            return AuthResult(success=False, headers={}, error_message=error)

        credentials = base64.b64encode(
            f"{self.username}:{self.password}".encode()
        ).decode()

        return AuthResult(
            success=True,
            headers={"Authorization": f"Basic {credentials}"}
        )


class OAuth2Auth(AuthStrategy):
    """OAuth2 authentication strategy."""

    def __init__(
        self,
        token_url: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        scope: Optional[str] = None
    ):
        self.token_url = token_url
        self.client_id = client_id or os.getenv("CHATBOT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("CHATBOT_CLIENT_SECRET")
        self.scope = scope or os.getenv("CHATBOT_OAUTH_SCOPE", "chatbot:read chatbot:write")
        self._cached_token: Optional[str] = None

    def validate_config(self) -> Tuple[bool, Optional[str]]:
        if not all([self.token_url, self.client_id, self.client_secret]):
            return False, "OAuth2 configuration incomplete. Required: token_url, client_id, client_secret"
        return True, None

    def _get_token(self) -> Optional[str]:
        """Fetch OAuth2 token from token endpoint."""
        try:
            response = requests.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": self.scope
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("access_token")
        except Exception as e:
            return None

    def authenticate(self) -> AuthResult:
        valid, error = self.validate_config()
        if not valid:
            return AuthResult(success=False, headers={}, error_message=error)

        if not self._cached_token:
            self._cached_token = self._get_token()

        if not self._cached_token:
            return AuthResult(
                success=False,
                headers={},
                error_message="Failed to obtain OAuth2 token"
            )

        return AuthResult(
            success=True,
            headers={"Authorization": f"Bearer {self._cached_token}"}
        )


class CustomHeadersAuth(AuthStrategy):
    """Custom headers authentication strategy."""

    def __init__(self, headers: Optional[Dict[str, str]] = None):
        self.headers = headers or {}
        env_headers = {
            "X-Custom-Auth": os.getenv("CHATBOT_CUSTOM_AUTH", "")
        }
        self.headers.update({k: v for k, v in env_headers.items() if v})

    def validate_config(self) -> Tuple[bool, Optional[str]]:
        if not self.headers:
            return False, "No custom headers provided."
        return True, None

    def authenticate(self) -> AuthResult:
        valid, error = self.validate_config()
        if not valid:
            return AuthResult(success=False, headers={}, error_message=error)

        return AuthResult(success=True, headers=self.headers)


class NoAuth(AuthStrategy):
    """No authentication strategy (public chatbots)."""

    def validate_config(self) -> Tuple[bool, Optional[str]]:
        return True, None

    def authenticate(self) -> AuthResult:
        return AuthResult(success=True, headers={})


class AuthFactory:
    """Factory for creating authentication strategies."""

    _strategies = {
        "api_key": APIKeyAuth,
        "bearer_token": BearerTokenAuth,
        "basic_auth": BasicAuth,
        "oauth2": OAuth2Auth,
        "custom_headers": CustomHeadersAuth,
        "none": NoAuth
    }

    @classmethod
    def create(cls, auth_type: str, **kwargs) -> AuthStrategy:
        """Create an authentication strategy by type."""
        strategy_class = cls._strategies.get(auth_type.lower())

        if strategy_class is None:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(
                f"Unknown auth type: '{auth_type}'. Available types: {available}"
            )

        return strategy_class(**kwargs)

    @classmethod
    def register_strategy(cls, name: str, strategy_class: type):
        """Register a custom authentication strategy."""
        cls._strategies[name.lower()] = strategy_class