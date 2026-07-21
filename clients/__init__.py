"""
Core chatbot client for ChatBot Tester Framework.
Provides a unified interface for interacting with chatbots.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import requests
from auth import AuthFactory, AuthStrategy


@dataclass
class Message:
    """Represents a chat message."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatResponse:
    """Represents a response from the chatbot."""
    message: Message
    raw_response: Any
    latency_ms: float
    status_code: int
    success: bool
    error: Optional[str] = None


@dataclass
class ConversationContext:
    """Maintains conversation history for context-aware testing."""
    messages: List[Message] = field(default_factory=list)
    system_prompt: Optional[str] = None

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to the conversation."""
        self.messages.append(Message(
            role=role,
            content=content,
            metadata=metadata or {}
        ))

    def clear(self):
        """Clear conversation history."""
        self.messages.clear()

    def to_dict(self) -> List[Dict[str, Any]]:
        """Convert conversation to list of message dicts."""
        return [
            {"role": m.role, "content": m.content}
            for m in self.messages
        ]


class ChatBotClient:
    """Main client for interacting with chatbots."""

    def __init__(
        self,
        base_url: str,
        auth_strategy: Optional[AuthStrategy] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip("/")
        self.auth_strategy = auth_strategy or NoAuth()
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers including authentication."""
        auth_result = self.auth_strategy.authenticate()
        if not auth_result.success:
            raise AuthenticationError(auth_result.error_message)

        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        default_headers.update(auth_result.headers)
        return default_headers

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        retries: int = 0
    ) -> requests.Response:
        """Make an HTTP request with retry logic."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        try:
            response = self._session.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            if retries < self.max_retries:
                return self._make_request(method, endpoint, data, retries + 1)
            raise ChatBotError(f"Request failed after {self.max_retries} retries: {e}")

    def send_message(
        self,
        message: Union[str, List[Dict]],
        conversation: Optional[ConversationContext] = None,
        context: Optional[Dict] = None
    ) -> ChatResponse:
        """
        Send a message to the chatbot.

        Args:
            message: String message or list of message dicts (multimodal)
            conversation: Optional conversation context
            context: Additional context metadata

        Returns:
            ChatResponse with the chatbot's reply
        """
        import time
        start_time = time.time()

        # Prepare request payload
        if isinstance(message, str):
            if conversation:
                payload_messages = conversation.to_dict() + [{"role": "user", "content": message}]
            else:
                payload_messages = [{"role": "user", "content": message}]
        else:
            payload_messages = message

        payload = {
            "messages": payload_messages,
        }
        if context:
            payload["context"] = context

        try:
            response = self._make_request("POST", "/api/v1/chat", payload)
            latency_ms = (time.time() - start_time) * 1000

            response_data = response.json()
            assistant_message = response_data.get("message", response_data.get("content", ""))

            if conversation:
                conversation.add_message("user", message if isinstance(message, str) else str(message))
                conversation.add_message("assistant", assistant_message)

            return ChatResponse(
                message=Message(role="assistant", content=assistant_message),
                raw_response=response_data,
                latency_ms=latency_ms,
                status_code=response.status_code,
                success=True
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return ChatResponse(
                message=Message(role="assistant", content=""),
                raw_response=None,
                latency_ms=latency_ms,
                status_code=0,
                success=False,
                error=str(e)
            )

    def reset_session(self) -> bool:
        """Reset the chatbot session."""
        try:
            response = self._make_request("POST", "/api/v1/reset")
            return response.status_code == 200
        except Exception:
            return False

    def health_check(self) -> Dict[str, Any]:
        """Check if the chatbot is healthy and responsive."""
        try:
            response = self._make_request("GET", "/api/v1/health")
            return {
                "healthy": True,
                "status_code": response.status_code,
                "response": response.json()
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class ChatBotError(Exception):
    """Raised when chatbot interaction fails."""
    pass


class ChatBotClientBuilder:
    """Builder for creating configured ChatBotClient instances."""

    def __init__(self):
        self.base_url: Optional[str] = None
        self.auth_type: Optional[str] = None
        self.auth_config: Dict[str, Any] = {}
        self.timeout: int = 30
        self.max_retries: int = 3

    def set_base_url(self, url: str) -> "ChatBotClientBuilder":
        self.base_url = url
        return self

    def set_auth(self, auth_type: str, **config) -> "ChatBotClientBuilder":
        self.auth_type = auth_type
        self.auth_config = config
        return self

    def set_timeout(self, timeout: int) -> "ChatBotClientBuilder":
        self.timeout = timeout
        return self

    def set_max_retries(self, retries: int) -> "ChatBotClientBuilder":
        self.max_retries = retries
        return self

    def build(self) -> ChatBotClient:
        if not self.base_url:
            raise ValueError("base_url is required")

        auth_strategy = None
        if self.auth_type:
            auth_strategy = AuthFactory.create(self.auth_type, **self.auth_config)

        return ChatBotClient(
            base_url=self.base_url,
            auth_strategy=auth_strategy,
            timeout=self.timeout,
            max_retries=self.max_retries
        )