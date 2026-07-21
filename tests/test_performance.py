"""
Performance tests for chatbot response times and load handling.
"""

import pytest
import time
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from clients import ChatBotClient, ConversationContext


class TestResponseTimes:
    """Test chatbot response time metrics."""

    @pytest.mark.performance
    def test_average_response_time(
        self,
        chatbot_client: ChatBotClient,
        performance_config: Dict[str, Any]
    ):
        """Test average response time is within threshold."""
        thresholds = performance_config.get("thresholds", {})
        p50_threshold = thresholds.get("p50", 500)  # milliseconds

        test_prompts = [
            "Hello!",
            "How are you?",
            "What can you help me with?",
            "Tell me about your features",
            "Thanks for your help"
        ]

        response_times = []
        for prompt in test_prompts:
            response = chatbot_client.send_message(prompt)
            if response.success:
                response_times.append(response.latency_ms)

        if response_times:
            avg_time = sum(response_times) / len(response_times)
            assert avg_time < p50_threshold, \
                f"Average response time {avg_time:.2f}ms exceeds threshold {p50_threshold}ms"

    @pytest.mark.performance
    @pytest.mark.parametrize("prompt", [
        "Hello",
        "What is 2+2?",
        "How do I reset my password?",
        "Tell me a joke",
        "Thank you"
    ])
    def test_response_time_distribution(
        self,
        chatbot_client: ChatBotClient,
        performance_config: Dict[str, Any],
        prompt: str
    ):
        """Test response time distribution across multiple runs."""
        thresholds = performance_config.get("thresholds", {})
        p95_threshold = thresholds.get("p95", 1000)

        response_times = []
        for _ in range(20):
            response = chatbot_client.send_message(prompt)
            if response.success:
                response_times.append(response.latency_ms)

        if response_times:
            response_times.sort()
            p95_index = int(len(response_times) * 0.95)
            p95_value = response_times[p95_index]

            assert p95_value < p95_threshold, \
                f"P95 response time {p95_value:.2f}ms exceeds threshold {p95_threshold}ms"

    @pytest.mark.performance
    def test_first_byte_time(self, chatbot_client: ChatBotClient):
        """Test time to first response (TTFB)."""
        # For streaming responses, measure time to first chunk
        start_time = time.time()
        response = chatbot_client.send_message("Tell me a long story")

        ttfb_ms = (time.time() - start_time) * 1000

        # TTFB should be reasonable for non-streaming
        assert ttfb_ms < 2000, f"Time to first byte {ttfb_ms:.2f}ms is too high"

        if response.success:
            assert response.latency_ms < 5000, "Overall response took too long"


class TestLoadTesting:
    """Test chatbot under load."""

    @pytest.mark.performance
    def test_concurrent_users(
        self,
        chatbot_client: ChatBotClient,
        performance_config: Dict[str, Any]
    ):
        """Test chatbot handles concurrent users."""
        concurrent_users = performance_config.get("concurrent_users", 10)
        requests_per_user = performance_config.get("requests_per_user", 5)

        test_message = "Test message for load testing"

        results = {"success": 0, "failed": 0, "total_time": 0}

        def send_requests(user_id: int):
            user_results = {"success": 0, "failed": 0, "times": []}
            for i in range(requests_per_user):
                start = time.time()
                response = chatbot_client.send_message(f"{test_message} from user {user_id}")
                elapsed = time.time() - start

                if response.success:
                    user_results["success"] += 1
                else:
                    user_results["failed"] += 1
                user_results["times"].append(elapsed * 1000)

            return user_results

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(send_requests, i) for i in range(concurrent_users)]

            for future in as_completed(futures):
                result = future.result()
                results["success"] += result["success"]
                results["failed"] += result["failed"]

        total_time = time.time() - start_time
        total_requests = concurrent_users * requests_per_user

        # All requests should complete
        assert results["success"] + results["failed"] == total_requests

        # Success rate should be high
        success_rate = results["success"] / total_requests
        assert success_rate > 0.9, \
            f"Success rate {success_rate:.2%} too low under load"

        # Average time per request should be reasonable
        avg_time_per_request = total_time / total_requests
        assert avg_time_per_request < 2, \
            f"Average time per request {avg_time_per_request:.2f}s too high"

    @pytest.mark.performance
    def test_sustained_load(
        self,
        chatbot_client: ChatBotClient,
        performance_config: Dict[str, Any]
    ):
        """Test chatbot handles sustained load over time."""
        ramp_up = performance_config.get("ramp_up_time", 5)
        duration = 30  # Run for 30 seconds

        start_time = time.time()
        request_count = 0
        error_count = 0

        while time.time() - start_time < duration:
            response = chatbot_client.send_message(f"Sustained load test message {request_count}")

            if response.success:
                request_count += 1
            else:
                error_count += 1

            # Brief pause between requests
            time.sleep(0.1)

        total_requests = request_count + error_count
        if total_requests > 0:
            error_rate = error_count / total_requests
            assert error_rate < 0.05, \
                f"Error rate {error_rate:.2%} too high during sustained load"

    @pytest.mark.performance
    def test_spike_handling(self, chatbot_client: ChatBotClient):
        """Test chatbot handles traffic spikes."""
        # Normal traffic first
        for _ in range(5):
            response = chatbot_client.send_message("Normal message")
            assert response.success

        # Spike
        spike_size = 20
        spike_results = {"success": 0, "failed": 0}

        with ThreadPoolExecutor(max_workers=spike_size) as executor:
            futures = [
                executor.submit(chatbot_client.send_message, f"Spike message {i}")
                for i in range(spike_size)
            ]

            for future in as_completed(futures):
                result = future.result()
                if result.success:
                    spike_results["success"] += 1
                else:
                    spike_results["failed"] += 1

        # Most spike requests should succeed
        spike_success_rate = spike_results["success"] / spike_size
        assert spike_success_rate > 0.7, \
            f"Spike success rate {spike_success_rate:.2%} too low"


class TestThroughput:
    """Test chatbot throughput metrics."""

    @pytest.mark.performance
    def test_requests_per_minute(
        self,
        chatbot_client: ChatBotClient
    ):
        """Test number of requests that can be handled per minute."""
        test_duration = 60  # 1 minute
        start_time = time.time()
        request_count = 0

        while time.time() - start_time < test_duration:
            response = chatbot_client.send_message(f"Throughput test {request_count}")
            if response.success:
                request_count += 1

        # Should handle at least 60 requests per minute (1 per second)
        assert request_count >= 60, \
            f"Throughput {request_count} rpm below minimum 60 rpm"

    @pytest.mark.performance
    def test_batch_processing(self, chatbot_client: ChatBotClient):
        """Test chatbot handles batch requests efficiently."""
        batch_size = 50
        prompts = [f"Batch message {i}" for i in range(batch_size)]

        start_time = time.time()

        for prompt in prompts:
            response = chatbot_client.send_message(prompt)
            assert response.success, f"Batch request {i} failed"

        total_time = time.time() - start_time
        avg_time_per_request = total_time / batch_size

        # Average should be under 1 second per request
        assert avg_time_per_request < 1.0, \
            f"Batch processing too slow: {avg_time_per_request:.2f}s per request"


class TestResourceUsage:
    """Test chatbot resource consumption."""

    @pytest.mark.performance
    def test_memory_efficiency(self, chatbot_client: ChatBotClient):
        """Test chatbot doesn't leak memory across requests."""
        # This is a simplified test - real memory testing would need psutil
        conversation = ConversationContext()

        initial_messages = len(conversation.messages)

        # Send many messages
        for i in range(100):
            chatbot_client.send_message(f"Message {i}", conversation=conversation)

        final_messages = len(conversation.messages)

        # Should have 100 user messages + responses
        assert final_messages > initial_messages + 100

        # If conversation context is cleared, messages should reset
        conversation.clear()
        assert len(conversation.messages) == 0, "Conversation clear failed"

    @pytest.mark.performance
    def test_connection_reuse(self, chatbot_client: ChatBotClient):
        """Test that connections are reused efficiently."""
        # Make multiple requests using same client
        start_time = time.time()

        for _ in range(10):
            response = chatbot_client.send_message("Connection test")
            assert response.success

        total_time = time.time() - start_time

        # Should complete quickly due to connection reuse
        assert total_time < 10, \
            f"Connection reuse not working efficiently: {total_time:.2f}s for 10 requests"


class TestPerformanceRegression:
    """Test for performance regressions."""

    @pytest.mark.performance
    def test_baseline_performance(self, chatbot_client: ChatBotClient):
        """Establish baseline performance metrics."""
        test_runs = 10
        response_times = []

        for _ in range(test_runs):
            response = chatbot_client.send_message("Baseline test")
            if response.success:
                response_times.append(response.latency_ms)

        if response_times:
            baseline = {
                "avg": sum(response_times) / len(response_times),
                "min": min(response_times),
                "max": max(response_times)
            }

            # Store baseline for future comparison
            # In real scenario, would compare against stored baselines
            assert baseline["avg"] < 1000, "Baseline performance too slow"
            assert baseline["max"] < 3000, "Baseline max response time too high"

    @pytest.mark.performance
    def test_performance_consistency(self, chatbot_client: ChatBotClient):
        """Test that response times are consistent (low variance)."""
        response_times = []

        for _ in range(20):
            response = chatbot_client.send_message("Consistency test")
            if response.success:
                response_times.append(response.latency_ms)

        if response_times and len(response_times) > 1:
            avg = sum(response_times) / len(response_times)
            variance = sum((t - avg) ** 2 for t in response_times) / len(response_times)
            std_dev = variance ** 0.5

            # Coefficient of variation should be low
            cv = std_dev / avg if avg > 0 else 0
            assert cv < 0.5, \
                f"High variance in response times (CV={cv:.2f}), suggests inconsistent performance"