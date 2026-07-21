"""
Chat Page Object - POM for chatbot conversation interface.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pom.pages.base_page import BasePageObject, UIElement
from clients import ChatBotClient, ConversationContext, ChatResponse
from locales import LocalizationManager, LocalizedConversationContext


class ChatPage(BasePageObject):
    """
    Page Object for chatbot conversation interface.
    Provides methods for interacting with chatbot through various interfaces.
    """

    def __init__(self, driver: Any = None, base_url: str = "", chat_endpoint: str = "/api/v1/chat"):
        super().__init__(driver, base_url)
        self.chat_endpoint = chat_endpoint
        self.localization_manager = LocalizationManager()
        self.conversation_context: Optional[ConversationContext] = None
        self._response_history: List[ChatResponse] = []

        # Register UI elements for web interface (if used)
        self._register_chat_elements()

    def _register_chat_elements(self):
        """Register common chat UI elements."""
        self.register_element(UIElement(
            name="message_input",
            locator_type="css",
            locator_value="textarea[name='message'], input[name='message'], #chat-input",
            description="Main message input field",
            is_critical=True
        ))
        self.register_element(UIElement(
            name="send_button",
            locator_type="css",
            locator_value="button[type='submit'], #send-button, .send-btn",
            description="Send message button",
            is_critical=True
        ))
        self.register_element(UIElement(
            name="chat_container",
            locator_type="css",
            locator_value="#chat-container, .messages, .chat-history",
            description="Chat messages container",
            is_critical=False
        ))
        self.register_element(UIElement(
            name="response_area",
            locator_type="css",
            locator_value=".response, .bot-message, .chat-response",
            description="Area where bot responses appear",
            is_critical=False
        ))
        self.register_element(UIElement(
            name="typing_indicator",
            locator_type="css",
            locator_value=".typing, .typing-indicator, .is-typing",
            description="Indicator shown when bot is typing",
            is_critical=False
        ))
        self.register_element(UIElement(
            name="error_message",
            locator_type="css",
            locator_value=".error, .error-message, #error",
            description="Error message display area",
            is_critical=False
        ))
        self.register_element(UIElement(
            name="status_indicator",
            locator_type="css",
            locator_value=".status, .connection-status",
            description="Connection status indicator",
            is_critical=False
        ))

    def wait_for_page_load(self, timeout: int = 30) -> bool:
        """
        Wait for chat page to load.

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if page loaded successfully
        """
        # For API-based testing, always return True
        # For web-based testing, implement specific checks
        self._page_load_time = datetime.now()
        return True

    def is_page_loaded(self) -> bool:
        """Check if chat page is loaded."""
        return self._page_load_time is not None

    def create_conversation(self) -> ConversationContext:
        """Create a new conversation context."""
        self.conversation_context = ConversationContext()
        return self.conversation_context

    def create_localized_conversation(self, locale: str = "en-US") -> LocalizedConversationContext:
        """
        Create a new localized conversation context.

        Args:
            locale: Locale code for the conversation

        Returns:
            LocalizedConversationContext instance
        """
        self.conversation_context = LocalizedConversationContext(
            locale=locale,
            localization_manager=self.localization_manager
        )
        return self.conversation_context

    def send_message(
        self,
        message: str,
        client: ChatBotClient,
        locale: str = "en-US",
        add_to_context: bool = True
    ) -> ChatResponse:
        """
        Send a message through the chatbot.

        Args:
            message: Message text to send
            client: ChatBotClient instance
            locale: Locale for the message
            add_to_context: Whether to add to conversation context

        Returns:
            ChatResponse from the chatbot
        """
        if add_to_context and self.conversation_context:
            response = client.send_message(
                message=message,
                conversation=self.conversation_context
            )
        else:
            response = client.send_message(message=message)

        self._response_history.append(response)
        return response

    def send_locale_aware_message(
        self,
        message_key: str,
        category: str,
        client: ChatBotClient,
        locale: str = "en-US"
    ) -> ChatResponse:
        """
        Send a message using localized content.

        Args:
            message_key: Key for the localized message
            category: Category of the message (e.g., "greetings", "questions")
            client: ChatBotClient instance
            locale: Locale code

        Returns:
            ChatResponse from the chatbot
        """
        message = self.localization_manager.get_translation(locale, message_key, category)
        return self.send_message(message, client, locale)

    def send_multiple_messages(
        self,
        messages: List[str],
        client: ChatBotClient,
        delay: float = 0.5
    ) -> List[ChatResponse]:
        """
        Send multiple messages in sequence.

        Args:
            messages: List of message texts
            client: ChatBotClient instance
            delay: Delay between messages in seconds

        Returns:
            List of ChatResponse objects
        """
        responses = []
        for message in messages:
            response = self.send_message(message, client)
            responses.append(response)

            if delay > 0 and messages.index(message) < len(messages) - 1:
                import time
                time.sleep(delay)

        return responses

    def send_locale_flow(
        self,
        flow_name: str,
        client: ChatBotClient,
        locale: str = "en-US"
    ) -> List[ChatResponse]:
        """
        Send a predefined flow of localized messages.

        Args:
            flow_name: Name of the flow (e.g., "greeting", "support")
            client: ChatBotClient instance
            locale: Locale code

        Returns:
            List of ChatResponse objects
        """
        flows = {
            "greeting": ["hello", "hi"],
            "support": ["help_me", "what_can_you_do"],
            "farewell": ["goodbye", "thank_you"]
        }

        keys = flows.get(flow_name, [])
        responses = []

        for key in keys:
            response = self.send_locale_aware_message(key, "greetings", client, locale)
            responses.append(response)

        return responses

    def reset_conversation(self, client: ChatBotClient) -> bool:
        """
        Reset the conversation context.

        Args:
            client: ChatBotClient instance

        Returns:
            True if reset successful
        """
        if self.conversation_context:
            self.conversation_context.clear()

        return client.reset_session()

    def get_response_history(self) -> List[ChatResponse]:
        """Get all responses from the conversation."""
        return self._response_history.copy()

    def get_last_response(self) -> Optional[ChatResponse]:
        """Get the most recent response."""
        return self._response_history[-1] if self._response_history else None

    def get_conversation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the conversation.

        Returns:
            Dictionary with conversation statistics
        """
        if not self._response_history:
            return {
                "message_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "avg_response_time_ms": 0,
                "total_duration_ms": 0
            }

        success_count = sum(1 for r in self._response_history if r.success)
        failure_count = len(self._response_history) - success_count
        response_times = [r.latency_ms for r in self._response_history if r.success]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        return {
            "message_count": len(self._response_history),
            "success_count": success_count,
            "failure_count": failure_count,
            "avg_response_time_ms": avg_response_time,
            "min_response_time_ms": min(response_times) if response_times else 0,
            "max_response_time_ms": max(response_times) if response_times else 0
        }

    def validate_response_content(
        self,
        response: ChatResponse,
        expected_keywords: List[str] = None,
        min_length: int = 0,
        max_length: int = None
    ) -> Dict[str, Any]:
        """
        Validate response content against criteria.

        Args:
            response: ChatResponse to validate
            expected_keywords: List of keywords that should be in response
            min_length: Minimum content length
            max_length: Maximum content length

        Returns:
            Validation result dictionary
        """
        content = response.message.content
        results = {
            "is_valid": True,
            "checks": {},
            "errors": []
        }

        # Check for expected keywords
        if expected_keywords:
            found_keywords = [kw for kw in expected_keywords if kw.lower() in content.lower()]
            missing_keywords = [kw for kw in expected_keywords if kw.lower() not in content.lower()]
            results["checks"]["keywords"] = {
                "found": found_keywords,
                "missing": missing_keywords,
                "passed": len(missing_keywords) == 0
            }
            if missing_keywords:
                results["is_valid"] = False
                results["errors"].append(f"Missing keywords: {missing_keywords}")

        # Check minimum length
        if min_length > 0:
            length_check = len(content) >= min_length
            results["checks"]["min_length"] = {
                "required": min_length,
                "actual": len(content),
                "passed": length_check
            }
            if not length_check:
                results["is_valid"] = False
                results["errors"].append(f"Content too short: {len(content)} < {min_length}")

        # Check maximum length
        if max_length:
            length_check = len(content) <= max_length
            results["checks"]["max_length"] = {
                "required": max_length,
                "actual": len(content),
                "passed": length_check
            }
            if not length_check:
                results["is_valid"] = False
                results["errors"].append(f"Content too long: {len(content)} > {max_length}")

        return results

    def verify_response_quality(self, response: ChatResponse) -> Dict[str, Any]:
        """
        Verify the quality of a response.

        Args:
            response: ChatResponse to verify

        Returns:
            Quality metrics dictionary
        """
        content = response.message.content
        words = content.split()

        quality_metrics = {
            "word_count": len(words),
            "character_count": len(content),
            "has_greeting": any(g in content.lower() for g in ["hello", "hi", "hey", "greetings"]),
            "has_farewell": any(f in content.lower() for f in ["bye", "goodbye", "thanks", "thank"]),
            "has_question_marks": "?" in content,
            "is_coherent": len(words) >= 3,  # Basic coherence check
            "has_url": "http" in content.lower(),
            "has_emoji": any(c in content for c in ["😀", "😊", "😂", "🤔", "👍"]),
            "quality_score": 0.0
        }

        # Calculate overall quality score
        score = 0.0
        if quality_metrics["is_coherent"]:
            score += 0.3
        if quality_metrics["has_greeting"]:
            score += 0.1
        if quality_metrics["has_farewell"]:
            score += 0.1
        if quality_metrics["character_count"] > 20:
            score += 0.2
        if quality_metrics["character_count"] > 100:
            score += 0.2
        if quality_metrics["has_question_marks"]:
            score += 0.1

        quality_metrics["quality_score"] = min(score, 1.0)

        return quality_metrics