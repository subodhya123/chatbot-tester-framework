"""
Utility functions for ChatBot Tester Framework.
"""

import hashlib
import json
import re
from typing import Any, Dict, List, Optional
from datetime import datetime


def sanitize_response(text: str) -> str:
    """Remove potentially harmful content from response."""
    patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\s*\(',
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    return text


def extract_metrics(response_text: str) -> Dict[str, Any]:
    """Extract numeric metrics from response."""
    metrics = {}
    numbers = re.findall(r'\d+(?:\.\d+)?', response_text)
    if numbers:
        metrics['numbers_found'] = [float(n) for n in numbers]
    return metrics


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple similarity between two texts."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union) if union else 0.0


def generate_test_id(prompt: str, category: str) -> str:
    """Generate unique test ID from prompt and category."""
    content = f"{prompt}:{category}:{datetime.now().isoformat()}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


def parse_conversation(messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Parse and validate conversation structure."""
    parsed = []
    for msg in messages:
        if 'role' in msg and 'content' in msg:
            parsed.append({
                'role': msg['role'],
                'content': msg['content'],
                'timestamp': datetime.now().isoformat()
            })
    return parsed


def check_response_quality(response: str) -> Dict[str, Any]:
    """Check response quality metrics."""
    quality = {
        'length': len(response),
        'word_count': len(response.split()),
        'has_question': '?' in response,
        'has_greeting': any(g in response.lower() for g in ['hi', 'hello', 'hey']),
        'is_empty': len(response.strip()) == 0
    }
    quality['quality_score'] = min(quality['length'] / 100, 1.0)
    return quality


def mask_sensitive_data(text: str) -> str:
    """Mask sensitive data patterns like emails, phone numbers."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
    text = re.sub(email_pattern, '[EMAIL]', text)
    text = re.sub(phone_pattern, '[PHONE]', text)
    return text


def format_duration(seconds: float) -> str:
    """Format duration in human readable format."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.0f}s"


class TestReportGenerator:
    """Generate structured test reports."""

    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    def add_result(self, test_name: str, passed: bool, duration: float, **kwargs):
        self.results.append({
            'test': test_name,
            'passed': passed,
            'duration': duration,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        })

    def generate_summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed

        return {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / total if total > 0 else 0,
            'duration_seconds': (datetime.now() - self.start_time).total_seconds(),
            'results': self.results
        }

    def to_json(self) -> str:
        return json.dumps(self.generate_summary(), indent=2)

    def to_markdown(self) -> str:
        summary = self.generate_summary()
        md = f"# Test Report\n\n"
        md += f"- **Total Tests**: {summary['total_tests']}\n"
        md += f"- **Passed**: {summary['passed']}\n"
        md += f"- **Failed**: {summary['failed']}\n"
        md += f"- **Pass Rate**: {summary['pass_rate']:.1%}\n\n"

        md += "## Test Results\n\n"
        md += "| Test | Status | Duration |\n"
        md += "|------|--------|----------|\n"

        for r in self.results:
            status = "PASS" if r['passed'] else "FAIL"
            md += f"| {r['test']} | {status} | {r['duration']:.2f}s |\n"

        return md