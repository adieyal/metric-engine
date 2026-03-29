# Contributing to Metric Engine

Thank you for your interest in contributing to Metric Engine! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- Use a clear and descriptive title
- Describe the exact steps to reproduce the problem
- Provide specific examples (minimal code snippets)
- Describe the behavior you observed and what you expected
- Include your environment details (Python version, OS, metric-engine version)

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md).

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- Use a clear and descriptive title
- Provide a detailed description of the proposed functionality
- Include code examples showing how the feature would be used
- Explain why this enhancement would be useful to most users

Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md).

### Improving Documentation

Documentation improvements are always welcome! This includes:

- Fixing typos or clarifying existing documentation
- Adding missing documentation for features
- Creating new tutorials or how-to guides
- Improving code examples

Use the [Documentation Issue template](.github/ISSUE_TEMPLATE/documentation.md).

### Pull Requests

1. Fork the repository and create your branch from `main`
2. Make your changes following the style guidelines
3. Add tests for any new functionality
4. Ensure all tests pass
5. Update documentation as needed
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- Virtual environment tool (venv, virtualenv, or conda)

### Setting Up Your Development Environment

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/metric-engine.git
cd metric-engine

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev,babel]"

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_value.py

# Run specific test
pytest tests/unit/test_value.py::test_construct_and_basic_repr_defaults

# Run with coverage
pytest --cov=src/metricengine --cov-report=term-missing

# Run tests for specific Python version (if you have multiple)
python3.11 -m pytest
```

### Code Quality Checks

```bash
# Lint code
make lint
# or
ruff check .

# Format code
ruff format .

# Type checking (if mypy is installed)
mypy src/metricengine

# Run all quality checks
make lint && pytest
```

### Building Documentation

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build documentation
make docs
# or
cd docs && python -m sphinx -b html . _build/html

# View documentation
open docs/_build/html/index.html  # macOS
xdg-open docs/_build/html/index.html  # Linux
start docs/_build/html/index.html  # Windows
```

## Coding Standards

### Python Style Guide

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Maximum line length: 88 characters (Black default)
- Use meaningful variable and function names

### Code Organization

```python
# Good
def calculate_gross_margin(revenue: FV[Money], cogs: FV[Money]) -> FV[Ratio]:
    """Calculate gross margin as (revenue - cogs) / revenue.

    Args:
        revenue: Total revenue
        cogs: Cost of goods sold

    Returns:
        Gross margin as a ratio
    """
    if revenue.is_none() or cogs.is_none():
        return FV.none_with_unit(Ratio)

    gross_profit = revenue - cogs
    return gross_profit / revenue
```

### Writing Tests

- Write tests for all new functionality
- Use descriptive test names: `test_<what>_<when>_<expected>`
- Follow AAA pattern: Arrange, Act, Assert
- Test edge cases (None values, zero, negative numbers)
- Test error conditions

```python
def test_division_by_zero_returns_none():
    """Test that dividing by zero returns None value."""
    # Arrange
    numerator = FV(100)
    denominator = FV(0)

    # Act
    result = numerator / denominator

    # Assert
    assert result.is_none()
```

### Documentation Standards

- All public functions/classes must have docstrings
- Use Google-style docstrings
- Include type information in docstrings
- Provide usage examples for complex functionality

```python
def calculate_metric(data: dict, policy: Policy | None = None) -> FV:
    """Calculate a metric from input data.

    This function processes financial data and returns a calculated metric
    using the provided policy for formatting and rounding.

    Args:
        data: Dictionary containing required input values
        policy: Optional policy for formatting. If None, uses DEFAULT_POLICY

    Returns:
        Calculated metric as a FinancialValue

    Raises:
        MissingInputError: If required inputs are not provided

    Example:
        >>> data = {"revenue": money(1000), "cost": money(600)}
        >>> result = calculate_metric(data)
        >>> print(result)
        400.00
    """
    pass
```

## Git Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```bash
feat(engine): add batch calculation support

Implement calculate_many method to efficiently compute multiple metrics
in a single pass with shared dependency resolution.

Closes #123
```

```bash
fix(value): correct __repr__ for is_percentage parameter

The __repr__ method was only including is_percentage when False,
but it should include it when True (non-default).

Fixes #456
```

## Project Structure

```
metric-engine/
├── src/metricengine/       # Main package
│   ├── value.py            # Core FinancialValue class
│   ├── units.py            # Unit system
│   ├── policy.py           # Policy configuration
│   ├── engine.py           # Calculation engine
│   ├── provenance.py       # Provenance tracking
│   ├── factories.py        # Convenience factories
│   ├── calculations/       # Built-in calculations
│   └── formatters/         # Formatting system
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   └── test_*.py           # Integration tests
├── docs/                   # Documentation
│   ├── concepts/           # Conceptual guides
│   ├── tutorials/          # Step-by-step tutorials
│   ├── howto/              # How-to guides
│   └── reference/          # API reference
├── examples/               # Example code
└── tools/                  # Development tools
```

## Adding New Features

### Checklist for New Features

- [ ] Feature implementation with type hints
- [ ] Unit tests with >90% coverage
- [ ] Integration tests if applicable
- [ ] Documentation in appropriate section
- [ ] Example usage in docstrings
- [ ] Update CHANGELOG.md
- [ ] Consider backward compatibility
- [ ] Update API reference if adding public API

### Adding New Calculations

1. Create your calculation function with decorator:

```python
from metricengine import calc, FV
from metricengine.units import Money, Ratio

@calc("my_metric", depends_on=("revenue", "cost"))
def my_metric(revenue: FV[Money], cost: FV[Money]) -> FV[Ratio]:
    """Calculate my custom metric."""
    return (revenue - cost) / revenue
```

2. Add tests:

```python
def test_my_metric_calculation():
    """Test my_metric calculation."""
    engine = Engine()
    data = {"revenue": money(1000), "cost": money(600)}
    result = engine.calculate("my_metric", data)
    assert result == ratio(0.4)
```

3. Add documentation in `docs/howto/` or `docs/tutorials/`

## Release Process

(Maintainers only)

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md with release date
3. Create release commit: `git commit -m "chore: bump version to X.Y.Z"`
4. Tag release: `git tag -a vX.Y.Z -m "Release version X.Y.Z"`
5. Push: `git push && git push --tags`
6. Build: `python -m build`
7. Upload to PyPI: `twine upload dist/*`
8. Create GitHub release with changelog excerpt

## Getting Help

- **Questions:** Open a Discussion on GitHub
- **Bugs:** Open an Issue with the Bug Report template
- **Features:** Open an Issue with the Feature Request template
- **Security:** See [SECURITY.md](SECURITY.md)

## Recognition

Contributors will be recognized in:
- The project's README.md contributors section
- Release notes for significant contributions
- Special thanks in documentation for major features

## License

By contributing to Metric Engine, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Metric Engine! 🎉
