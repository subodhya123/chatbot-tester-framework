"""
Mock ChatBot Server for testing the ChatBot Tester Framework.
Simulates a real chatbot API with various responses and behaviors.
"""

import json
import time
import random
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuration
CONFIG = {
    "version": "1.0.0",
    "uptime": 3600,
    "max_tokens": 1000,
    "temperature": 0.7
}

# Conversation storage (in-memory for demo)
conversations = {}


def get_conversation_id():
    """Generate a unique conversation ID."""
    return f"conv_{int(time.time() * 1000)}"


def get_client_ip():
    """Get client IP from request."""
    return request.headers.get('X-Forwarded-For', request.remote_addr)


class MockChatBot:
    """Mock chatbot with configurable responses."""

    def __init__(self):
        self.greetings = {
            "en-US": ["Hello! How can I help you today?", "Hi there! What can I do for you?"],
            "es-ES": ["¡Hola! ¿Cómo puedo ayudarte hoy?", "¡Hola! ¿Qué puedo hacer por ti?"],
            "fr-FR": ["Bonjour! Comment puis-je vous aider?", "Salut! Que puis-je faire pour vous?"],
            "de-DE": ["Hallo! Wie kann ich Ihnen helfen?", "Hi! Was kann ich für Sie tun?"],
            "zh-CN": ["你好！今天我能帮你什么？", "嗨！我能为你做什么？"],
            "ar-SA": ["مرحبا! كيف يمكنني مساعدتك اليوم؟", "مرحبا! ما الذي يمكنني فعله لك؟"]
        }

        self.farewells = {
            "en-US": ["Goodbye! Have a great day!", "Bye! Take care!"],
            "es-ES": ["¡Adiós! ¡Que tengas un buen día!", "¡Hasta luego!"],
            "fr-FR": ["Au revoir! Bonne journée!", "À bientôt!"],
            "de-DE": ["Auf Wiedersehen! Haben Sie einen schönen Tag!", "Bis später!"],
            "zh-CN": ["再见！祝你有美好的一天！", "回头见！"],
            "ar-SA": ["وداعا! أتمنى لك يوماً رائعاً!", "إلى اللقاء!"]
        }

        self.responses = {
            "how_are_you": {
                "en-US": "I'm doing well, thank you for asking! How can I assist you today?",
                "es-ES": "Estoy bien, gracias por preguntar. ¿Cómo puedo ayudarte?",
                "fr-FR": "Je vais bien, merci de demander! Comment puis-je vous aider?",
                "de-DE": "Mir geht es gut, danke der Nachfrage! Wie kann ich helfen?",
                "zh-CN": "我很好，谢谢关心！我今天能帮你什么？",
                "ar-SA": "أنا بخير، شكراً لسؤالك! كيف يمكنني مساعدتك؟"
            },
            "what_is_your_name": {
                "en-US": "My name is ChatBot Tester. I'm an AI assistant ready to help you!",
                "es-ES": "Mi nombre es ChatBot Tester. ¡Soy un asistente de IA listo para ayudarte!",
                "fr-FR": "Je m'appelle ChatBot Tester. Je suis un assistant IA prêt à vous aider!",
                "de-DE": "Mein Name ist ChatBot Tester. Ich bin ein KI-Assistent, der Ihnen helfen möchte!",
                "zh-CN": "我叫 ChatBot Tester。我是一个AI助手，随时准备帮助你！",
                "ar-SA": "اسمي ChatBot Tester. أنا مساعد ذكاء اصطناعي مستعد لمساعدتك!"
            },
            "what_can_you_do": {
                "en-US": "I can help with a variety of tasks including: answering questions, providing information, helping with problems, and having conversations. What would you like help with?",
                "es-ES": "Puedo ayudar con varias tareas incluyendo: responder preguntas, proporcionar información, ayudar con problemas y tener conversaciones. ¿Con qué te gustaría ayuda?",
                "fr-FR": "Je peux aider avec diverses tâches: répondre aux questions, fournir des informations, aider avec des problèmes et avoir des conversations. Avec quoi puis-je vous aider?",
                "de-DE": "Ich kann bei verschiedenen Aufgaben helfen: Fragen beantworten, Informationen bereitstellen, bei Problemen helfen und Konversationen führen. Wobei kann ich helfen?",
                "zh-CN": "我可以帮助完成各种任务，包括：回答问题、提供信息、帮助解决问题和进行对话。你想要什么帮助？",
                "ar-SA": "أستطيع المساعدة في مجموعة متنوعة من المهام包括:回答问题、提供信息、帮助解决问题和进行对话。你想要什么帮助؟"
            }
        }

    def get_response(self, message: str, locale: str = "en-US") -> str:
        """Get appropriate response for message and locale."""
        message_lower = message.lower().strip()

        # Check for greetings
        greeting_words = ["hello", "hi", "hey", "hola", "bonjour", "hallo", "你好", "مرحبا"]
        if any(greeting in message_lower for greeting in greeting_words):
            greetings = self.greetings.get(locale, self.greetings["en-US"])
            return random.choice(greetings)

        # Check for farewells
        farewell_words = ["bye", "goodbye", "adios", "au revoir", "auf wiedersehen", "再见", "وداعا"]
        if any(farewell in message_lower for farewell in farewell_words):
            farewells = self.farewells.get(locale, self.farewells["en-US"])
            return random.choice(farewells)

        # Check for specific questions
        if "how are you" in message_lower:
            return self.responses["how_are_you"].get(locale, self.responses["how_are_you"]["en-US"])

        if "your name" in message_lower or "name" in message_lower:
            return self.responses["what_is_your_name"].get(locale, self.responses["what_is_your_name"]["en-US"])

        if "what can you do" in message_lower or "help me" in message_lower:
            return self.responses["what_can_you_do"].get(locale, self.responses["what_can_you_do"]["en-US"])

        # Default response
        default_responses = {
            "en-US": f"I received your message: '{message[:50]}...'. How can I help you further?",
            "es-ES": f"Recibí tu mensaje: '{message[:50]}...'. ¿Cómo puedo ayudarte más?",
            "fr-FR": f"J'ai reçu votre message: '{message[:50]}...'. Comment puis-je vous aider davantage?",
            "de-DE": f"Ich habe Ihre Nachricht erhalten: '{message[:50]}...'. Wie kann ich Ihnen weiterhelfen?",
            "zh-CN": f"我收到了你的消息：'{message[:50]}...'。我还能怎么帮助你？",
            "ar-SA": f"تلقت رسالتك: '{message[:50]}...'. كيف يمكنني مساعدتك أكثر؟"
        }

        return default_responses.get(locale, default_responses["en-US"])

    def detect_injection(self, message: str) -> bool:
        """Check for potential injection attempts."""
        dangerous_patterns = [
            "DROP TABLE", "'; DROP", "1' OR '1'='1",
            "<script>", "javascript:", "onerror=",
            "ignore previous", "you are now", "override"
        ]
        message_upper = message.upper()
        return any(pattern.upper() in message_upper for pattern in dangerous_patterns)

    def sanitize_response(self, response: str) -> str:
        """Sanitize response content."""
        # Basic sanitization
        dangerous = ["<script>", "javascript:", "onerror="]
        for d in dangerous:
            response = response.replace(d, "")
        return response


# Initialize mock chatbot
mock_bot = MockChatBot()


@app.route("/api/v1/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    # Simulate slight delay
    time.sleep(random.uniform(0.01, 0.05))

    return jsonify({
        "healthy": True,
        "status": "ok",
        "version": CONFIG["version"],
        "uptime": CONFIG["uptime"],
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route("/api/v1/chat", methods=["POST"])
def chat():
    """Main chat endpoint."""
    start_time = time.time()

    try:
        data = request.get_json()

        if not data or "messages" not in data:
            return jsonify({
                "error": "Invalid request",
                "message": "Missing 'messages' in request body"
            }), 400

        messages = data["messages"]
        context = data.get("context", {})
        locale = context.get("locale", "en-US")

        # Get the last user message
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            return jsonify({
                "error": "Invalid request",
                "message": "No user message found"
            }), 400

        # Check for injection attempts
        if mock_bot.detect_injection(user_message):
            return jsonify({
                "error": "Content policy violation",
                "message": "Your message contains prohibited content."
            }), 400

        # Simulate processing time
        processing_time = random.uniform(0.1, 0.5)
        time.sleep(processing_time)

        # Get response
        response_text = mock_bot.get_response(user_message, locale)
        response_text = mock_bot.sanitize_response(response_text)

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000

        return jsonify({
            "message": response_text,
            "conversation_id": context.get("conversation_id", get_conversation_id()),
            "latency_ms": round(latency_ms, 2),
            "tokens_used": len(response_text.split()),
            "model": "mock-chatbot-v1"
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route("/api/v1/reset", methods=["POST"])
def reset_session():
    """Reset conversation endpoint."""
    time.sleep(random.uniform(0.01, 0.05))

    return jsonify({
        "success": True,
        "message": "Session reset successfully"
    }), 200


@app.route("/api/v1/settings", methods=["GET"])
def get_settings():
    """Get settings endpoint."""
    return jsonify({
        "language": "en-US",
        "theme": "auto",
        "notifications": True,
        "sound_enabled": True
    }), 200


@app.route("/api/v1/settings", methods=["PATCH"])
def update_settings():
    """Update settings endpoint."""
    data = request.get_json() or {}

    return jsonify({
        "success": True,
        "updated_settings": data
    }), 200


@app.route("/api/v1/settings/reset", methods=["POST"])
def reset_settings():
    """Reset settings to defaults."""
    return jsonify({
        "success": True,
        "message": "Settings reset to defaults"
    }), 200


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found", "message": str(e)}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error", "message": str(e)}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("Mock ChatBot Server for ChatBot Tester Framework")
    print("=" * 60)
    print("Starting server on http://localhost:8000")
    print("")
    print("Endpoints:")
    print("  GET  /api/v1/health  - Health check")
    print("  POST /api/v1/chat    - Send message")
    print("  POST /api/v1/reset   - Reset session")
    print("  GET  /api/v1/settings - Get settings")
    print("  PATCH /api/v1/settings - Update settings")
    print("")
    print("Supported locales: en-US, es-ES, fr-FR, de-DE, zh-CN, ar-SA")
    print("=" * 60)

    app.run(host="0.0.0.0", port=8000, debug=False, threaded=True)