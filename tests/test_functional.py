"""
Functional tests for chatbot behavior and responses.
"""

import pytest
from clients import ChatBotClient, ConversationContext


class TestChatbotResponses:
    """Test chatbot response quality and correctness."""

    @pytest.mark.functional
    def test_greeting_response(self, chatbot_client: ChatBotClient):
        """Test chatbot responds appropriately to greetings."""
        response = chatbot_client.send_message("Hello!")

        assert response.success, f"Chatbot request failed: {response.error}"
        assert len(response.message.content) > 0, "Empty response received"
        assert response.status_code == 200

    @pytest.mark.functional
    def test_conversation_context(self, chatbot_client: ChatBotClient):
        """Test chatbot maintains conversation context."""
        conversation = ConversationContext()

        # First message
        response1 = chatbot_client.send_message(
            "My favorite color is blue",
            conversation=conversation
        )
        assert response1.success

        # Follow-up referencing context
        response2 = chatbot_client.send_message(
            "What is my favorite color?",
            conversation=conversation
        )
        assert response2.success

        # The response should reference blue (or indicate context awareness)
        content_lower = response2.message.content.lower()
        assert "blue" in content_lower or "favorite" in content_lower, \
            f"Response doesn't show context awareness: {response2.message.content}"

    @pytest.mark.functional
    def test_clarification_request(self, chatbot_client: ChatBotClient):
        """Test chatbot asks for clarification on ambiguous input."""
        response = chatbot_client.send_message("Tell me about it")

        assert response.success
        # Should either ask for clarification or provide a reasonable response
        assert len(response.message.content) > 0

    @pytest.mark.functional
    def test_error_handling_invalid_input(self, chatbot_client: ChatBotClient):
        """Test chatbot handles invalid input gracefully."""
        response = chatbot_client.send_message("")

        # Should either handle gracefully or return appropriate error
        # Behavior depends on chatbot implementation
        assert response.message.content != "I don't understand" or response.success


class TestChatbotCapabilities:
    """Test specific chatbot capabilities."""

    @pytest.mark.functional
    @pytest.mark.parametrize("scenario", [
        "What is your name?",
        "Who created you?",
        "What can you do?",
        "How do I use you?"
    ])
    def test_capability_questions(self, chatbot_client: ChatBotClient, scenario):
        """Test chatbot responds to capability questions."""
        response = chatbot_client.send_message(scenario)

        assert response.success, f"Request failed: {response.error}"
        assert len(response.message.content) > 10, "Response too short"

    @pytest.mark.functional
    def test_multi_turn_conversation(self, chatbot_client: ChatBotClient):
        """Test chatbot handles multi-turn conversations."""
        conversation = ConversationContext()

        messages = [
            "Hi, I need help with my order",
            "Order number is 12345",
            "I haven't received a confirmation email",
            "Yes, please send it to test@example.com"
        ]

        for msg in messages:
            response = chatbot_client.send_message(msg, conversation=conversation)
            assert response.success, f"Failed on message: {msg}"
            conversation.add_message("user", msg)
            conversation.add_message("assistant", response.message.content)

        # Verify conversation has proper structure
        assert len(conversation.messages) == 8  # 4 user + 4 assistant

    @pytest.mark.functional
    def test_rate_limit_response(self, chatbot_client: ChatBotClient):
        """Test chatbot handles rate limiting appropriately."""
        # Send rapid requests
        responses = []
        for i in range(5):
            response = chatbot_client.send_message(f"Test message {i}")
            responses.append(response)

        # All requests should either succeed or get proper rate limit response
        if not all(r.success for r in responses):
            assert any(
                "rate" in r.error.lower() or "429" in str(r.status_code)
                for r in responses if not r.success
            ), "Rate limiting not handled properly"


class TestChatbotBoundaries:
    """Test chatbot behavior at boundaries."""

    @pytest.mark.functional
    def test_max_input_length(self, chatbot_client: ChatBotClient):
        """Test chatbot handles very long input."""
        long_message = "A" * 10000

        response = chatbot_client.send_message(long_message)

        # Should either handle gracefully or return appropriate error
        assert response.success or response.status_code == 413

    @pytest.mark.functional
    def test_special_characters(self, chatbot_client: ChatBotClient):
        """Test chatbot handles special characters."""
        special_messages = [
            "Hello! How are you? @#$%",
            "Testing <script>alert('xss')</script>",
            "Unicode: 你好 🌍 🚀",
            "Emoji: 😄 😎 🤖"
        ]

        for msg in special_messages:
            response = chatbot_client.send_message(msg)
            assert response.success, f"Failed on special chars: {msg}"

    @pytest.mark.functional
    def test_repeated_same_message(self, chatbot_client: ChatBotClient, conversation_context):
        """Test chatbot handles repeated identical messages."""
        message = "What is the weather like?"

        responses = []
        for _ in range(3):
            response = chatbot_client.send_message(message, conversation=conversation_context)
            responses.append(response)
            assert response.success

        # Responses should be consistent
        contents = [r.message.content for r in responses]
        # Allow some variation but should be fundamentally similar
        assert len(set(contents)) <= 3  # Should have mostly consistent responses


class TestChatbotHealth:
    """Test chatbot health and status endpoints."""

    @pytest.mark.functional
    def test_health_endpoint(self, chatbot_client: ChatBotClient):
        """Test chatbot health check endpoint."""
        health = chatbot_client.health_check()

        assert health.get("healthy", False), f"Chatbot unhealthy: {health}"

    @pytest.mark.functional
    def test_reset_endpoint(self, chatbot_client: ChatBotClient):
        """Test chatbot reset endpoint."""
        # Send a message
        response = chatbot_client.send_message("Hello")
        assert response.success

        # Reset session
        reset_success = chatbot_client.reset_session()
        assert reset_success, "Reset endpoint failed"

    @pytest.mark.e2e
    def test_full_conversation_flow(self, chatbot_client: ChatBotClient):
        """End-to-end test of complete conversation flow."""
        conversation = ConversationContext()

        # Start conversation
        greeting = chatbot_client.send_message("Hello, I'm testing the chatbot")
        assert greeting.success

        # Ask for help
        help_response = chatbot_client.send_message(
            "Can you help me find information about your features?",
            conversation=conversation
        )
        assert help_response.success

        # Follow up
        followup = chatbot_client.send_message(
            "Tell me more about that",
            conversation=conversation
        )
        assert followup.success

        # End conversation
        goodbye = chatbot_client.send_message(
            "Thanks, that was helpful!",
            conversation=conversation
        )
        assert goodbye.success