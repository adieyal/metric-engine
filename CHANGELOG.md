# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD pipeline with multi-version Python testing
- Issue and pull request templates
- Comprehensive project infrastructure (CHANGELOG, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT)
- Test isolation improvements

### Fixed
- Fixed `FinancialValue.__repr__()` to correctly show `is_percentage` parameter when True
- Fixed babel integration test to handle comma separators in formatted output

### Changed
- Updated project structure for better maintainability

## [0.1.0] - 2025-01-XX

### Added
- **Core Features**
  - Strongly-typed financial values with `FinancialValue` (FV) class
  - Support for Money, Ratio, and Percent units
  - Decimal precision throughout to avoid floating-point errors
  - Immutable value objects with safe arithmetic operations
  - Policy-driven formatting and rounding behavior
  - Null-safe operations (division by zero returns None instead of crashing)

- **Calculation Engine**
  - Dependency-driven calculation system with automatic resolution
  - DAG-based execution with topological ordering
  - Circular dependency detection
  - Batch calculation support (`calculate_many`)
  - Per-metric policy configuration
  - Extensible calculation registry

- **Provenance Tracking** (Major Feature)
  - Automatic calculation traceability for audit trails
  - Complete provenance graphs with tamper-evident hashing
  - Human-readable calculation explanations via `explain()`
  - JSON export of full calculation history via `to_trace_json()`
  - Metadata support for adding context to calculations
  - Configurable provenance behavior (performance vs. completeness)
  - Memory-efficient provenance with caching

- **Unit System**
  - Built-in unit types: Money, Ratio, Percent, Dimensionless
  - Extensible unit system with `NewUnit` for custom units
  - Unit conversion support with automatic tracking
  - Unit arithmetic safety (prevents invalid operations)
  - Unit-aware formatting

- **Policy System**
  - Configurable decimal places and rounding modes
  - Custom null text display
  - Percent display formatting (decimal vs. percentage)
  - Context-based policy resolution
  - Policy inheritance in operations

- **Formatting & Internationalization**
  - Built-in formatters for Money, Percent, Ratio
  - Optional Babel integration for locale-aware formatting
  - Currency symbol support
  - Thousands separators and grouping
  - Custom rendering system with pluggable renderers
  - DisplayPolicy for rich formatting options

- **Framework Integration**
  - Plugin architecture via entry points
  - Django integration stub (foundation for future development)
  - Extensible integration system

- **Built-in Calculation Libraries**
  - Profitability calculations (gross profit, margins, EBITDA, etc.)
  - Ratios (current ratio, quick ratio, debt-to-equity, etc.)
  - Pricing calculations (markup, margin, discount, etc.)
  - Unit economics (CAC, LTV, payback period, etc.)
  - Inventory calculations (turnover, days, etc.)
  - Growth calculations (CAGR, growth rate, etc.)
  - Variance analysis
  - Rules-based calculations

- **Developer Experience**
  - Comprehensive test suite (1,300+ tests)
  - Type hints throughout for IDE support
  - Detailed documentation (60+ pages)
  - Multiple tutorials and how-to guides
  - Example code in `/examples` directory
  - Factory functions for convenient value creation

- **Documentation**
  - Quickstart guide
  - Concept documentation (values, units, policy, engine, provenance)
  - Tutorials for common scenarios
  - How-to guides for specific tasks
  - API reference documentation
  - Design documentation for advanced topics
  - Sphinx-based documentation site

### Design Decisions
- **Immutability**: All values are immutable to prevent unexpected side effects
- **Decimal-based**: Uses Python's `Decimal` type throughout for precision
- **None propagation**: Invalid operations return `None` values instead of raising exceptions (configurable)
- **Policy-driven**: Behavior is configured via policies rather than global settings
- **Provenance-first**: Calculation traceability is built-in, not bolted on

### Known Issues
- Test isolation issues with provenance global state (39 tests fail in full suite but pass individually)
- Django integration is minimal (stub only)
- Documentation mentions features not yet published to ReadTheDocs

### Breaking Changes
- None (initial release)

## Release Notes

### Version 0.1.0 - Initial Alpha Release

This is the first public release of Metric Engine. It provides a solid foundation for building financial applications with type-safe calculations, comprehensive provenance tracking, and extensible calculation frameworks.

**Key Highlights:**
- ✨ Complete provenance tracking system for audit trails
- 🎯 1,300+ tests ensuring reliability
- 📚 Comprehensive documentation
- 🔧 Extensible calculation engine
- 💯 Decimal precision throughout

**Target Audience:** Python developers building financial applications, business analytics tools, or any system requiring precise calculations with audit trails.

**Python Compatibility:** Python 3.9, 3.10, 3.11, 3.12

**Installation:** `pip install metric-engine`

---

[Unreleased]: https://github.com/adieyal/metric-engine/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/adieyal/metric-engine/releases/tag/v0.1.0
