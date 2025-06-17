# Contributing to Multi-Chain Portfolio Dashboard

Thank you for your interest in contributing to this demo project!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/multichain-portfolio-dashboard.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Set up the development environment:
   ```bash
   uv venv .venv
   source .venv/bin/activate
   uv pip install -r requirements/development.txt
   cp .env.example .env
   python manage.py migrate
   python manage.py generate_mock_data
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use type hints where possible
- Run `ruff check .` before committing
- Run `mypy .` for type checking

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb: "Add", "Fix", "Update", "Remove"
- Keep the first line under 50 characters
- Add detailed description if needed

### Testing

- Write tests for new features
- Ensure all tests pass: `pytest`
- Maintain test coverage above 80%

### Pull Request Process

1. Update the README.md with details of changes if needed
2. Update requirements if you add dependencies
3. Ensure all tests pass and linting is clean
4. Create a Pull Request with a clear description

## What to Contribute

- Bug fixes
- New blockchain integrations
- Performance improvements
- Documentation improvements
- UI/UX enhancements
- Test coverage improvements

## Questions?

Feel free to open an issue for any questions about contributing!