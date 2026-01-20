.PHONY: test test-unit test-contracts test-golden test-integration test-slow test-all install lint format

# Install dependencies
install:
	pip install -e ".[dev]"

# Run all fast tests (unit + contracts)
test:
	pytest tests/test_parsing.py tests/test_analyzer_mocked.py tests/test_contracts.py -v

# Run only unit tests (parsing, no mocks)
test-unit:
	pytest tests/test_parsing.py -v

# Run contract tests
test-contracts:
	pytest tests/test_contracts.py -v

# Run mock-based tests
test-mocked:
	pytest tests/test_analyzer_mocked.py -v

# Run golden sample tests
test-golden:
	pytest tests/test_golden_samples.py -v

# Run integration tests (requires ANTHROPIC_API_KEY)
test-integration:
	pytest tests/test_integration.py -v --tb=long

# Run LLM-as-judge tests (slow, requires ANTHROPIC_API_KEY)
test-slow:
	pytest tests/test_llm_judge.py -v --tb=long -m slow

# Run all tests
test-all:
	pytest tests/ -v

# Run tests with coverage
test-coverage:
	pytest tests/ --cov=src/code_tutor --cov-report=term-missing --cov-report=html

# Lint code
lint:
	ruff check src/ tests/

# Format code
format:
	black src/ tests/
	ruff check --fix src/ tests/

# Run metrics report (after test run)
metrics-report:
	python -c "from tests.metrics import MetricsTracker, create_test_run_metrics; \
		tracker = MetricsTracker('./test_metrics'); \
		metrics = create_test_run_metrics(); \
		print(tracker.generate_report(metrics))"

# Help
help:
	@echo "Available targets:"
	@echo "  install          - Install dependencies"
	@echo "  test             - Run fast tests (unit + contracts + mocked)"
	@echo "  test-unit        - Run unit tests only"
	@echo "  test-contracts   - Run contract tests"
	@echo "  test-mocked      - Run mock-based tests"
	@echo "  test-golden      - Run golden sample tests"
	@echo "  test-integration - Run integration tests (requires API key)"
	@echo "  test-slow        - Run LLM-as-judge tests (requires API key)"
	@echo "  test-all         - Run all tests"
	@echo "  test-coverage    - Run tests with coverage report"
	@echo "  lint             - Run linter"
	@echo "  format           - Format code"
