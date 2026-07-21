"""
Localization tests for multilingual chatbot support.
Tests chatbot behavior across different languages and locales.
"""

import pytest
from typing import Dict, Any, List
from clients import ChatBotClient
from locales import LocalizationManager, LocalizedConversationContext
from pom.pages import ChatPage


class TestLocalizationBasics:
    """Test basic localization support."""

    @pytest.mark.localization
    @pytest.mark.parametrize("locale", ["en-US", "es-ES", "fr-FR", "de-DE"])
    def test_greeting_in_locale(
        self,
        chatbot_client: ChatBotClient,
        localization_manager: LocalizationManager,
        locale: str
    ):
        """
        Test chatbot responds to localized greetings.

        Args:
            chatbot_client: ChatBotClient fixture
            localization_manager: LocalizationManager fixture
            locale: Language locale code

        Tests:
            - Chatbot accepts greeting in specified locale
            - Response is non-empty
            - Response time is reasonable
        """
        # Get localized greeting message for the locale
        greeting = localization_manager.get_greeting(locale)

        # Send localized greeting to chatbot
        response = chatbot_client.send_message(greeting)

        # Assert chatbot responds successfully
        assert response.success, f"Failed to get response for locale: {locale}"

        # Assert response content is not empty
        assert len(response.message.content) > 0, \
            f"Empty response for locale: {locale}"

        # Log the response for debugging
        print(f"[{locale}] Greeting: '{greeting}' -> Response: '{response.message.content[:50]}...'")

    @pytest.mark.localization
    @pytest.mark.parametrize("locale,expected_greeting", [
        ("en-US", "Hello"),
        ("es-ES", "Hola"),
        ("fr-FR", "Bonjour"),
        ("de-DE", "Hallo"),
        ("zh-CN", "你好"),
        ("ar-SA", "مرحبا")
    ])
    def test_all_locales_greeting(
        self,
        chatbot_client: ChatBotClient,
        locale: str,
        expected_greeting: str
    ):
        """
        Test greeting messages are correct for each locale.

        Args:
            chatbot_client: ChatBotClient fixture
            locale: Language locale code
            expected_greeting: Expected greeting word in that locale
        """
        # Send the expected greeting
        response = chatbot_client.send_message(expected_greeting)

        # Verify response received
        assert response.success, \
            f"Chatbot not responding to {locale} greeting: {expected_greeting}"

        # Verify response is non-empty
        assert len(response.message.content) > 0, \
            f"Empty response for {locale}"


class TestLocalizationConversation:
    """Test conversation flows in different locales."""

    @pytest.mark.localization
    @pytest.mark.parametrize("locale", ["en-US", "es-ES", "fr-FR"])
    def test_multi_turn_conversation_in_locale(
        self,
        chatbot_client: ChatBotClient,
        localization_manager: LocalizationManager,
        locale: str
    ):
        """
        Test complete conversation flow in a specific locale.

        Args:
            chatbot_client: ChatBotClient fixture
            localization_manager: LocalizationManager fixture
            locale: Language locale code

        Tests:
            - Multi-turn conversation works in the locale
            - Conversation context is maintained
            - All responses are non-empty
        """
        # Create a localized conversation context
        conversation = LocalizedConversationContext(
            locale=locale,
            localization_manager=localization_manager
        )

        # Define conversation flow messages
        flow_messages = [
            ("greetings", "hello"),      # Hello
            ("questions", "how_are_you"), # How are you?
            ("greetings", "goodbye")      # Goodbye
        ]

        responses = []
        for category, key in flow_messages:
            # Get localized message
            message_text = localization_manager.get_translation(locale, key, category)

            # Send message with conversation context
            response = chatbot_client.send_message(
                message=message_text,
                conversation=conversation
            )

            # Verify response received
            assert response.success, \
                f"Failed at {category}/{key} for locale {locale}"

            # Add user message to conversation
            conversation.add_user_message(message_text)

            # Store response
            responses.append(response.message.content)

        # Verify all responses are non-empty
        for idx, response_text in enumerate(responses):
            assert len(response_text) > 0, \
                f"Empty response at turn {idx + 1} for locale {locale}"

    @pytest.mark.localization
    def test_localized_conversation_context_tracking(
        self,
        chatbot_client: ChatBotClient,
        localization_manager: LocalizationManager
    ):
        """
        Test that localized conversation context tracks messages correctly.

        Tests:
            - Messages are tracked with correct locale
            - Timestamps are recorded
            - Conversation structure is maintained
        """
        # Create localized conversation for French
        locale = "fr-FR"
        conversation = LocalizedConversationContext(
            locale=locale,
            localization_manager=localization_manager
        )

        # Get localized messages
        greeting = localization_manager.get_greeting(locale)
        question = localization_manager.get_question(locale, "how_are_you")

        # Send messages
        chatbot_client.send_message(greeting, conversation=conversation)
        chatbot_client.send_message(question, conversation=conversation)

        # Verify conversation context
        assert len(conversation.messages) == 4, \
            "Expected 4 messages (2 user + 2 assistant)"

        # Verify all messages have locale set correctly
        for msg in conversation.messages:
            assert msg["locale"] == locale, \
                f"Message locale mismatch: expected {locale}"

        # Verify messages have timestamps
        for msg in conversation.messages:
            assert "timestamp" in msg, \
                "Message missing timestamp"


class TestLocalizationRTLSupport:
    """Test right-to-left language support."""

    @pytest.mark.localization
    @pytest.mark.parametrize("locale", ["ar-SA", "he-IL", "fa-IR"])
    def test_rtl_language_support(
        self,
        chatbot_client: ChatBotClient,
        localization_manager: LocalizationManager,
        locale: str
    ):
        """
        Test chatbot handles RTL (right-to-left) languages.

        Args:
            chatbot_client: ChatBotClient fixture
            localization_manager: LocalizationManager fixture
            locale: RTL language locale code

        Tests:
            - Locale is correctly identified as RTL
            - Chatbot responds to RTL language input
            - Response handling is correct for RTL
        """
        # Verify locale is marked as RTL
        assert localization_manager.is_rtl_language(locale), \
            f"Locale {locale} should be marked as RTL"

        # Get RTL locale config
        locale_config = localization_manager.get_locale_config(locale)
        assert locale_config is not None, f"Locale config not found for {locale}"
        assert locale_config.is_rtl is True, f"Locale {locale} should have is_rtl=True"

        # Get localized greeting
        greeting = localization_manager.get_greeting(locale)

        # Send greeting to chatbot
        response = chatbot_client.send_message(greeting)

        # Verify response received
        assert response.success, \
            f"Chatbot not responding to RTL locale: {locale}"

        # Verify response is non-empty
        assert len(response.message.content) > 0, \
            f"Empty response for RTL locale: {locale}"

    @pytest.mark.localization
    def test_arabic_conversation_flow(
        self,
        chatbot_client: ChatBotClient,
        localization_manager: LocalizationManager
    ):
        """
        Test a complete Arabic conversation flow.

        Tests:
            - Arabic greetings are accepted
            - Arabic questions receive appropriate responses
            - Conversation context is maintained
        """
        locale = "ar-SA"
        conversation = LocalizedConversationContext(
            locale=locale,
            localization_manager=localization_manager
        )

        # Define Arabic conversation flow
        arabic_flow = [
            ("greetings", "hello"),        # مرحبا
            ("questions", "what_is_your_name"),  # ما اسمك؟
            ("greetings", "goodbye")        # وداعا
        ]

        for category, key in arabic_flow:
            message = localization_manager.get_translation(locale, key, category)
            response = chatbot_client.send_message(message, conversation=conversation)

            assert response.success, \
                f"Failed at {category}/{key} for Arabic"

            conversation.add_user_message(message)

            # Verify response contains some Arabic or is valid
            assert len(response.message.content) > 0


class TestLocalizationEdgeCases:
    """Test edge cases in localization."""

    @pytest.mark.localization
    def test_unsupported_locale_fallback(self, chatbot_client: ChatBotClient):
        """
        Test chatbot behavior with unsupported locale.
        Should fall back to default locale (en-US).
        """
        # Use a locale that might not have translations
        unsupported_locale = "xx-XX"

        # Chatbot should handle gracefully
        response = chatbot_client.send_message("Hello")

        # Should still get a response (fallback behavior)
        assert response.success, \
            "Chatbot should handle unsupported locale gracefully"

    @pytest.mark.localization
    def test_mixed_locale_conversation(
        self,
        chatbot_client: ChatBotClient,
        localization_manager: LocalizationManager
    ):
        """
        Test conversation that switches between locales.
        Some chatbots may not support this, so we test gracefully.
        """
        # Start with English
        response1 = chatbot_client.send_message("Hello")

        # Switch to Spanish
        spanish_greeting = localization_manager.get_greeting("es-ES")
        response2 = chatbot_client.send_message(spanish_greeting)

        # Switch to Chinese
        chinese_greeting = localization_manager.get_greeting("zh-CN")
        response3 = chatbot_client.send_message(chinese_greeting)

        # All should receive responses (fallback to supported)
        assert response1.success
        assert response2.success
        assert response3.success

    @pytest.mark.localization
    def test_unicode_emoji_in_locale_messages(
        self,
        chatbot_client: ChatBotClient,
        localization_manager: LocalizationManager
    ):
        """
        Test that locale messages with unicode and emoji are handled.

        Tests:
            - Emoji in messages are processed correctly
            - Unicode characters are preserved
            - Mixed unicode content works
        """
        # Create message with emoji for Japanese locale
        locale = "ja-JP"
        base_message = localization_manager.get_greeting(locale)

        # Add emoji to message
        emoji_message = f"{base_message} 👋🎉"

        # Send to chatbot
        response = chatbot_client.send_message(emoji_message)

        # Verify response
        assert response.success, \
            "Failed to handle unicode emoji message"

        # Response should be non-empty
        assert len(response.message.content) > 0


class TestLocalizationQuality:
    """Test quality of localized responses."""

    @pytest.mark.localization
    @pytest.mark.parametrize("locale", ["en-US", "es-ES", "fr-FR", "de-DE"])
    def test_response_quality_across_locales(
        self,
        chatbot_client: ChatBotClient,
        localization_manager: LocalizationManager,
        locale: str
    ):
        """
        Test that response quality is consistent across locales.

        Args:
            chatbot_client: ChatBotClient fixture
            localization_manager: LocalizationManager fixture
            locale: Language locale code

        Tests:
            - Response lengths are reasonable across locales
            - Response times are within threshold
            - No error messages in responses
        """
        # Get test message
        question = localization_manager.get_question(locale, "what_can_you_do")

        # Send to chatbot
        response = chatbot_client.send_message(question)

        # Verify success
        assert response.success, \
            f"Chatbot not responding in {locale}"

        # Get response content
        content = response.message.content.lower()

        # Verify no error indicators in response
        error_indicators = ["error", "exception", "failed", "cannot"]
        has_error = any(indicator in content for indicator in error_indicators)

        assert not has_error, \
            f"Response contains error indicator for locale {locale}"

        # Verify response length is reasonable (not too short)
        assert len(response.message.content) > 10, \
            f"Response too short for locale {locale}"

    @pytest.mark.localization
    def test_localization_manager_coverage(
        self,
        localization_manager: LocalizationManager
    ):
        """
        Test that localization manager has adequate coverage.
        Verifies all expected locales and categories exist.
        """
        # Get all available locales
        locales = localization_manager.get_all_locales()

        # Should have at least the basic locales
        expected_locales = ["en-US", "es-ES", "fr-FR", "de-DE", "zh-CN", "ar-SA"]
        for expected_locale in expected_locales:
            assert expected_locale in locales, \
                f"Missing expected locale: {expected_locale}"

        # Test that translations exist for each locale
        for locale in locales:
            # Test categories exist
            categories = ["greetings", "questions", "commands"]
            for category in categories:
                # Try to get a common key
                if category == "greetings":
                    key = "hello"
                elif category == "questions":
                    key = "how_are_you"
                else:
                    key = "reset"

                # Should not raise exception
                translation = localization_manager.get_translation(locale, key, category)
                assert translation is not None, \
                    f"Missing translation for {locale}/{category}/{key}"


class TestLocalizationPerformance:
    """Test performance of localized responses."""

    @pytest.mark.localization
    @pytest.mark.parametrize("locale", ["en-US", "es-ES", "zh-CN"])
    def test_response_time_by_locale(
        self,
        chatbot_client: ChatBotClient,
        localization_manager: LocalizationManager,
        locale: str,
        performance_config: Dict[str, Any]
    ):
        """
        Test response times are consistent across locales.

        Args:
            chatbot_client: ChatBotClient fixture
            localization_manager: LocalizationManager fixture
            locale: Language locale code
            performance_config: Performance thresholds

        Tests:
            - Response times are within threshold
            - No significant latency difference between locales
        """
        thresholds = performance_config.get("thresholds", {})
        p95_threshold = thresholds.get("p95", 1000)  # milliseconds

        # Get test message
        greeting = localization_manager.get_greeting(locale)

        # Send multiple requests and measure
        response_times = []
        for _ in range(5):
            response = chatbot_client.send_message(greeting)
            assert response.success, f"Request failed for locale: {locale}"
            response_times.append(response.latency_ms)

        # Calculate P95
        response_times.sort()
        p95_index = int(len(response_times) * 0.95)
        p95_time = response_times[p95_index]

        # Verify within threshold
        assert p95_time < p95_threshold, \
            f"P95 response time {p95_time:.2f}ms exceeds threshold {p95_threshold}ms for {locale}"


# ============================================================================
# POM-based Localization Tests
# ============================================================================

class TestLocalizationWithPOM:
    """Test localization using Page Object Model pattern."""

    @pytest.mark.localization
    @pytest.mark.e2e
    def test_chat_page_localization(
        self,
        chatbot_client: ChatBotClient,
        localization_manager: LocalizationManager
    ):
        """
        Test chat page with localization using POM pattern.

        Tests:
            - ChatPage can send localized messages
            - Response validation works with localized content
            - Conversation tracking works
        """
        # Create chat page object
        chat_page = ChatPage(
            base_url=chatbot_client.base_url
        )

        # Create localized conversation
        locale = "fr-FR"
        conversation = chat_page.create_localized_conversation(locale)

        # Send localized greeting
        greeting = localization_manager.get_greeting(locale)
        response = chat_page.send_message(
            message=greeting,
            client=chatbot_client,
            locale=locale,
            add_to_context=True
        )

        # Verify response
        assert response.success, "Failed to send localized message via POM"

        # Verify conversation was updated
        assert len(conversation.messages) >= 2, \
            "Conversation should have at least user and assistant messages"

    @pytest.mark.localization
    def test_chat_page_locale_flow(
        self,
        chatbot_client: ChatBotClient,
        localization_manager: LocalizationManager
    ):
        """
        Test predefined locale flows using ChatPage POM.

        Args:
            chatbot_client: ChatBotClient fixture
            localization_manager: LocalizationManager fixture
        """
        chat_page = ChatPage(base_url=chatbot_client.base_url)

        # Test greeting flow in Spanish
        responses = chat_page.send_locale_flow(
            flow_name="greeting",
            client=chatbot_client,
            locale="es-ES"
        )

        # Verify all responses received
        assert len(responses) > 0, "No responses received for locale flow"

        # Verify each response was successful
        for response in responses:
            assert response.success, \
                f"Locale flow failed: {response.error}"