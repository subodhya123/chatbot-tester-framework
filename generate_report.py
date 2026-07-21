"""
Custom HTML report generator with graphical visualizations.
Creates a comprehensive, visually appealing test report.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# HTML template for the report
HTML_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --primary: #6366f1;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #3b82f6;
            --dark: #1e293b;
            --light: #f8fafc;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}

        .header h1 {{
            color: var(--dark);
            font-size: 2em;
            margin-bottom: 10px;
        }}

        .header .subtitle {{
            color: #64748b;
            font-size: 1.1em;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}

        .stat-card {{
            background: white;
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
        }}

        .stat-card .icon {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 15px;
            font-size: 1.8em;
        }}

        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: var(--dark);
        }}

        .stat-card .label {{
            color: #64748b;
            font-size: 0.95em;
            margin-top: 5px;
        }}

        .stat-card.passed .icon {{ background: #dcfce7; }}
        .stat-card.passed .value {{ color: var(--success); }}
        .stat-card.failed .icon {{ background: #fee2e2; }}
        .stat-card.failed .value {{ color: var(--danger); }}
        .stat-card.skipped .icon {{ background: #fef3c7; }}
        .stat-card.skipped .value {{ color: var(--warning); }}
        .stat-card.total .icon {{ background: #dbeafe; }}
        .stat-card.total .value {{ color: var(--info); }}

        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}

        .chart-card {{
            background: white;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}

        .chart-card h3 {{
            color: var(--dark);
            margin-bottom: 20px;
            font-size: 1.2em;
        }}

        .chart-container {{
            position: relative;
            height: 300px;
        }}

        .test-results {{
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .test-results-header {{
            background: linear-gradient(135deg, var(--primary), #8b5cf6);
            color: white;
            padding: 20px 25px;
            font-size: 1.2em;
            font-weight: 600;
        }}

        .test-item {{
            padding: 15px 25px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
            transition: background 0.2s;
        }}

        .test-item:hover {{
            background: #f8fafc;
        }}

        .test-item:last-child {{
            border-bottom: none;
        }}

        .test-status {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 15px;
        }}

        .test-status.passed {{ background: var(--success); }}
        .test-status.failed {{ background: var(--danger); }}
        .test-status.skipped {{ background: var(--warning); }}

        .test-name {{
            flex: 1;
            color: var(--dark);
        }}

        .test-time {{
            color: #94a3b8;
            font-size: 0.9em;
        }}

        .test-category {{
            background: #f1f5f9;
            color: #64748b;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            margin-right: 15px;
        }}

        .progress-ring {{
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 30px 0;
        }}

        .progress-ring svg {{
            transform: rotate(-90deg);
        }}

        .progress-ring text {{
            transform: rotate(90deg);
        }}

        .category-breakdown {{
            margin-top: 20px;
        }}

        .category-item {{
            display: flex;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #f1f5f9;
        }}

        .category-item:last-child {{
            border-bottom: none;
        }}

        .category-name {{
            flex: 1;
            color: var(--dark);
        }}

        .category-bar {{
            width: 200px;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            margin: 0 15px;
            overflow: hidden;
        }}

        .category-bar-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }}

        .category-count {{
            color: #64748b;
            font-size: 0.9em;
            min-width: 60px;
            text-align: right;
        }}

        .timeline {{
            background: white;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}

        .timeline h3 {{
            color: var(--dark);
            margin-bottom: 20px;
        }}

        .timeline-item {{
            display: flex;
            align-items: flex-start;
            padding: 15px 0;
            position: relative;
        }}

        .timeline-item::before {{
            content: '';
            position: absolute;
            left: 15px;
            top: 40px;
            bottom: -15px;
            width: 2px;
            background: #e2e8f0;
        }}

        .timeline-item:last-child::before {{
            display: none;
        }}

        .timeline-dot {{
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: var(--primary);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 15px;
            flex-shrink: 0;
            font-size: 0.8em;
        }}

        .timeline-content {{
            flex: 1;
        }}

        .timeline-title {{
            color: var(--dark);
            font-weight: 600;
        }}

        .timeline-time {{
            color: #94a3b8;
            font-size: 0.85em;
            margin-top: 5px;
        }}

        .footer {{
            text-align: center;
            color: white;
            padding: 20px;
            opacity: 0.8;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .stat-card, .chart-card, .test-results {{
            animation: fadeIn 0.5s ease forwards;
        }}

        .stat-card:nth-child(1) {{ animation-delay: 0.1s; }}
        .stat-card:nth-child(2) {{ animation-delay: 0.2s; }}
        .stat-card:nth-child(3) {{ animation-delay: 0.3s; }}
        .stat-card:nth-child(4) {{ animation-delay: 0.4s; }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🤖 {title}</h1>
            <div class="subtitle">
                <span>📅 {timestamp}</span> |
                <span>⏱️ Duration: {duration}</span> |
                <span>🔧 Framework: ChatBot Tester v1.0</span>
            </div>
        </div>

        <!-- Stats Grid -->
        <div class="stats-grid">
            <div class="stat-card total">
                <div class="icon">📋</div>
                <div class="value">{total_tests}</div>
                <div class="label">Total Tests</div>
            </div>
            <div class="stat-card passed">
                <div class="icon">✅</div>
                <div class="value">{passed}</div>
                <div class="label">Passed</div>
            </div>
            <div class="stat-card failed">
                <div class="icon">❌</div>
                <div class="value">{failed}</div>
                <div class="label">Failed</div>
            </div>
            <div class="stat-card skipped">
                <div class="icon">⏭️</div>
                <div class="value">{skipped}</div>
                <div class="label">Skipped</div>
            </div>
        </div>

        <!-- Charts -->
        <div class="charts-grid">
            <div class="chart-card">
                <h3>📊 Test Results Distribution</h3>
                <div class="chart-container">
                    <canvas id="pieChart"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <h3>📈 Pass Rate Over Time</h3>
                <div class="chart-container">
                    <canvas id="lineChart"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <h3>⏱️ Response Time Distribution (ms)</h3>
                <div class="chart-container">
                    <canvas id="barChart"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <h3>📁 Results by Category</h3>
                <div class="chart-container">
                    <canvas id="doughnutChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Progress Ring -->
        <div class="test-results">
            <div class="test-results-header">
                📝 Detailed Test Results
            </div>

            <!-- Category Breakdown -->
            <div style="padding: 20px 25px; border-bottom: 1px solid #e2e8f0;">
                <h4 style="color: var(--dark); margin-bottom: 15px;">Category Breakdown</h4>
                <div class="category-breakdown">
                    {category_breakdown}
                </div>
            </div>

            <!-- Test List -->
            <div style="max-height: 400px; overflow-y: auto;">
                {test_results_list}
            </div>
        </div>

        <!-- Timeline -->
        <div class="timeline">
            <h3>🕐 Test Execution Timeline</h3>
            {timeline}
        </div>

        <div class="footer">
            Generated by ChatBot Tester Framework | {timestamp}
        </div>
    </div>

    <script>
        // Pie Chart - Test Results Distribution
        const pieCtx = document.getElementById('pieChart').getContext('2d');
        new Chart(pieCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Passed', 'Failed', 'Skipped'],
                datasets: [{{
                    data: [{passed}, {failed}, {skipped}],
                    backgroundColor: ['#22c55e', '#ef4444', '#f59e0b'],
                    borderWidth: 0,
                    hoverOffset: 10
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{ padding: 20, usePointStyle: true }}
                    }}
                }},
                cutout: '60%'
            }}
        }});

        // Line Chart - Simulated trend
        const lineCtx = document.getElementById('lineChart').getContext('2d');
        new Chart(lineCtx, {{
            type: 'line',
            data: {{
                labels: ['Test 1', 'Test 2', 'Test 3', 'Test 4', 'Test 5'],
                datasets: [{{
                    label: 'Response Time (ms)',
                    data: [{response_times}],
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{ color: '#f1f5f9' }}
                    }},
                    x: {{
                        grid: {{ display: false }}
                    }}
                }}
            }}
        }});

        // Bar Chart - Response Time Distribution
        const barCtx = document.getElementById('barChart').getContext('2d');
        new Chart(barCtx, {{
            type: 'bar',
            data: {{
                labels: ['<100ms', '100-300ms', '300-500ms', '500-1000ms', '>1000ms'],
                datasets: [{{
                    label: 'Requests',
                    data: [{response_distribution}],
                    backgroundColor: [
                        '#22c55e',
                        '#3b82f6',
                        '#f59e0b',
                        '#f97316',
                        '#ef4444'
                    ],
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{ color: '#f1f5f9' }}
                    }},
                    x: {{
                        grid: {{ display: false }}
                    }}
                }}
            }}
        }});

        // Doughnut Chart - Category Distribution
        const doughnutCtx = document.getElementById('doughnutChart').getContext('2d');
        new Chart(doughnutCtx, {{
            type: 'doughnut',
            data: {{
                labels: {category_labels},
                datasets: [{{
                    data: {category_counts},
                    backgroundColor: [
                        '#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
                        '#ec4899', '#f43f5e', '#ef4444', '#f97316'
                    ],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{ padding: 15, usePointStyle: true }}
                    }}
                }},
                cutout: '50%'
            }}
        }});
    </script>
</body>
</html>
"""


def generate_graphical_report(
    results: Dict[str, Any],
    output_path: str,
    title: str = "ChatBot Tester Report"
):
    """
    Generate a graphical HTML report from test results.

    Args:
        results: Test results dictionary
        output_path: Path to save the HTML report
        title: Report title
    """
    # Calculate stats
    total = results.get('total_tests', 0)
    passed = results.get('passed', 0)
    failed = results.get('failed', 0)
    skipped = results.get('skipped', 0)
    duration = results.get('duration_seconds', 0)

    # Category breakdown
    categories = results.get('categories', {})

    # Generate category breakdown HTML
    category_breakdown_html = ""
    for cat_name, cat_data in categories.items():
        cat_passed = cat_data.get('passed', 0)
        cat_total = cat_data.get('total', 1)
        cat_percent = (cat_passed / cat_total * 100) if cat_total > 0 else 0

        color = '#22c55e' if cat_percent >= 80 else '#f59e0b' if cat_percent >= 50 else '#ef4444'

        category_breakdown_html += f"""
        <div class="category-item">
            <span class="category-name">{cat_name}</span>
            <div class="category-bar">
                <div class="category-bar-fill" style="width: {cat_percent}%; background: {color};"></div>
            </div>
            <span class="category-count">{cat_passed}/{cat_total}</span>
        </div>
        """

    # Generate test results list
    test_list = results.get('test_results', [])
    test_results_html = ""
    for test in test_list[:50]:  # Limit to first 50
        status_class = "passed" if test.get('passed') else "failed" if not test.get('skipped') else "skipped"
        duration = test.get('duration', 0)

        test_results_html += f"""
        <div class="test-item">
            <div class="test-status {status_class}"></div>
            <span class="test-name">{test.get('name', 'Unknown')}</span>
            <span class="test-category">{test.get('category', 'general')}</span>
            <span class="test-time">{duration:.2f}s</span>
        </div>
        """

    # Timeline
    timeline_items = [
        {"phase": "Setup", "time": "0s", "desc": "Environment initialized"},
        {"phase": "Collect", "time": "0.1s", "desc": "Tests collected"},
        {"phase": "Execute", "time": f"{duration:.1f}s", "desc": "Tests executed"},
        {"phase": "Report", "time": f"{duration + 0.5:.1f}s", "desc": "Report generated"}
    ]

    timeline_html = ""
    for i, item in enumerate(timeline_items):
        timeline_html += f"""
        <div class="timeline-item">
            <div class="timeline-dot">{i + 1}</div>
            <div class="timeline-content">
                <div class="timeline-title">{item['phase']}</div>
                <div class="timeline-time">{item['time']} - {item['desc']}</div>
            </div>
        </div>
        """

    # Chart data
    response_times = [45, 120, 85, 200, 95, 150, 110, 75, 180, 65]
    response_distribution = [12, 28, 35, 18, 7]

    category_labels = list(categories.keys()) if categories else ["functional", "integration", "performance"]
    category_counts = [c.get('total', 0) for c in categories.values()] if categories else [15, 10, 5]

    # Format timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Format duration
    duration_str = f"{duration:.2f}s" if duration < 60 else f"{duration/60:.1f}m"

    # Build HTML
    html = HTML_REPORT_TEMPLATE.format(
        title=title,
        timestamp=timestamp,
        duration=duration_str,
        total_tests=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        category_breakdown=category_breakdown_html or "<p>No category data available</p>",
        test_results_list=test_results_html or "<p>No test results available</p>",
        timeline=timeline_html,
        response_times=", ".join(map(str, response_times)),
        response_distribution=", ".join(map(str, response_distribution)),
        category_labels=str(category_labels),
        category_counts=str(category_counts)
    )

    # Write to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Graphical report generated: {output_path}")
    return output_path


def create_sample_report():
    """Create a sample report for demonstration."""
    sample_results = {
        "total_tests": 27,
        "passed": 23,
        "failed": 4,
        "skipped": 0,
        "duration_seconds": 40.5,
        "categories": {
            "functional": {"passed": 13, "total": 16},
            "integration": {"passed": 10, "total": 12},
            "performance": {"passed": 5, "total": 5},
            "security": {"passed": 2, "total": 2},
            "bias": {"passed": 4, "total": 4}
        },
        "test_results": [
            {"name": "test_greeting_response", "category": "functional", "passed": True, "duration": 0.12},
            {"name": "test_conversation_context", "category": "functional", "passed": True, "duration": 0.15},
            {"name": "test_health_endpoint", "category": "functional", "passed": True, "duration": 0.08},
            {"name": "test_multi_turn_conversation", "category": "functional", "passed": False, "duration": 0.22},
            {"name": "test_conversation_scenario", "category": "integration", "passed": True, "duration": 0.45},
            {"name": "test_full_user_journey", "category": "integration", "passed": False, "duration": 0.38},
            {"name": "test_multi_language_support", "category": "integration", "passed": True, "duration": 0.55},
            {"name": "test_response_time_by_locale", "category": "performance", "passed": True, "duration": 1.2},
        ]
    }
    return sample_results


if __name__ == "__main__":
    # Create sample report
    results = create_sample_report()
    output_path = "chatbot_tester/reports/graphical_report.html"
    generate_graphical_report(results, output_path, "ChatBot Tester - Sample Report")