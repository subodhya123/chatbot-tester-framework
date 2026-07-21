# Contributing to ChatBot Tester Framework

Thank you for your interest in contributing!

## How to Contribute

### Reporting Issues

- Check existing issues before creating new ones
- Provide detailed information including:
  - Your configuration (config.yaml)
  - Python version
  - Operating system
  - Steps to reproduce

### Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass: `pytest`
6. Commit with clear messages: `git commit -m "Add feature: description"`
7. Push and create a Pull Request

### Coding Standards

- Follow PEP 8
- Add docstrings to all new functions and classes
- Keep functions focused and small
- Use type hints where possible
- Add pytest markers to new tests

### Testing Guidelines

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=chatbot_tester

# Run specific test types
pytest -m functional
pytest -m performance
pytest -m security
pytest -m bias

# Generate HTML report
pytest --html=reports/report.html --self-contained-html
```

### Documentation

- Update README.md for user-facing changes
- Add docstrings for new public APIs
- Update this CONTRIBUTING.md if process changes

## Questions?

Open an issue for discussion before starting significant changes.