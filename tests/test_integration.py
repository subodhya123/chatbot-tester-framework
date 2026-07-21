"""
Example integration tests demonstrating the framework's capabilities.
"""

import pytest
from clients import ChatBotClient, ConversationContext


class TestChatbotIntegration:
    """Integration tests for real-world scenarios."""

    @pytest.mark.integration
    @pytest.mark.parametrize("scenario", [
        {"name": "customer_support", "messages": [
            "Hi, I need help",
            "I can't log into my account",
            "I already tried resetting my password",
            "Yes, I'm still having the issue"
        ]},
        {"name": "product_inquiry", "messages": [
            "What products do you offer?",
            "Tell me about your pricing",
            "Is there a free trial?",
            "How do I sign up?"
        ]},
        {"name": "technical_support", "messages": [
            "My app is not working",
            "It keeps crashing when I open settings",
            "I tried reinstalling but it didn't help",
            "I'm using iPhone 12 with latest OS"
        ]}
    ])
    def test_conversation_scenario(
        self,
        chatbot_client: ChatBotClient,
        scenario: dict
    ):
        """Test a complete conversation scenario."""
        conversation = ConversationContext()
        responses = []

        for message in scenario["messages"]:
            response = chatbot_client.send_message(
                message,
                conversation=conversation
            )
            assert response.success, f"Failed at: {message}"
            responses.append(response.message.content)
            conversation.add_message("user", message)
            conversation.add_message("assistant", response.message.content)

        # Verify conversation completed
        assert len(responses) == len(scenario["messages"])

    @pytest.mark.e2e
    def test_full_user_journey(self, chatbot_client: ChatBotClient):
        """Test complete user journey through the chatbot."""
        conversation = ConversationContext()

        # Discovery
        greeting = chatbot_client.send_message("Hello, what can you do?")
        assert greeting.success

        # Engagement
        feature = chatbot_client.send_message(
            "Tell me more about your features",
            conversation=conversation
        )
        assert feature.success

        # Action
        signup = chatbot_client.send_message(
            "How do I get started?",
            conversation=conversation
        )
        assert signup.success

        # Resolution
        thanks = chatbot_client.send_message(
            "Thanks, that was helpful!",
            conversation=conversation
        )
        assert thanks.success

        # Verify conversation length
        assert len(conversation.messages) == 8

    @pytest.mark.integration
    def test_multi_language_support(self, chatbot_client: ChatBotClient):
        """Test chatbot handles multiple languages."""
        languages = {
            "English": "Hello",
            "Spanish": "Hola",
            "French": "Bonjour",
            "German": "Guten Tag",
            "Japanese": "こんにちは"
        }

        for lang, greeting in languages.items():
            response = chatbot_client.send_message(greeting)
            assert response.success, f"Failed for {lang}"
            assert len(response.message.content) > 0

    @pytest.mark.integration
    def test_error_recovery(self, chatbot_client: ChatBotClient):
        """Test chatbot recovers gracefully from errors."""
        conversation = ConversationContext()

        # Normal interaction
        response1 = chatbot_client.send_message(
            "Hello",
            conversation=conversation
        )
        assert response1.success

        # Reset session
        chatbot_client.reset_session()
        conversation.clear()

        # Continue after reset
        response2 = chatbot_client.send_message(
            "Hello again",
            conversation=conversation
        )
        assert response2.success


class TestChatbotEdgeCases:
    """Test edge cases and unusual inputs."""

    @pytest.mark.integration
    def test_very_long_conversation(self, chatbot_client: ChatBotClient):
        """Test chatbot handles very long conversations."""
        conversation = ConversationContext()

        # 50 message exchange
        for i in range(50):
            response = chatbot_client.send_message(
                f"Message {i}",
                conversation=conversation
            )
            assert response.success

        assert len(conversation.messages) == 100  # 50 user + 50 assistant

    @pytest.mark.integration
    def test_rapid_fire_messages(self, chatbot_client: ChatBotClient):
        """Test chatbot handles rapid successive messages."""
        responses = []
        for i in range(20):
            response = chatbot_client.send_message(f"Rapid message {i}")
            responses.append(response)

        # Most should succeed
        success_count = sum(1 for r in responses if r.success)
        assert success_count > 15  # At least 75% success rate

    @pytest.mark.integration
    def test_concurrent_conversations(self, chatbot_client: ChatBotClient):
        """Test handling multiple concurrent conversation contexts."""
        conversations = [ConversationContext() for _ in range(5)]

        for conv in conversations:
            response = chatbot_client.send_message(
                f"Context: {id(conv)}",
                conversation=conv
            )
            assert response.success

            # Add a follow-up
            response2 = chatbot_client.send_message(
                "Follow-up question",
                conversation=conv
            )
            assert response2.success

    @pytest.mark.integration
    def test_empty_and_null_inputs(self, chatbot_client: ChatBotClient):
        """Test chatbot handles empty and null inputs gracefully."""
        # Empty string
        response1 = chatbot_client.send_message("")
        assert response1.success or response1.status_code in [400, 422]

        # Whitespace only
        response2 = chatbot_client.send_message("   ")
        assert response2.success

    @pytest.mark.integration
    def test_unicode_and_emoji(self, chatbot_client: ChatBotClient):
        """Test chatbot handles unicode and emoji properly."""
        test_inputs = [
            "Hello 👋",
            "🎉🎊✨",
            "こんにちは",
            "🎄🎁",
            "مرحبا"
        ]

        for test_input in test_inputs:
            response = chatbot_client.send_message(test_input)
            assert response.success, f"Failed on: {test_input}"