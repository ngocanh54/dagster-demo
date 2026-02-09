.PHONY: install dev test clean clean-all help venv

VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Default target
help:
	@echo "Dagster Demo - Available Commands"
	@echo "=================================="
	@echo "make install    - Create venv and install dependencies"
	@echo "make dev        - Start Dagster webserver (like 'airflow webserver')"
	@echo "make test       - Run tests"
	@echo "make clean      - Remove build artifacts and cache files"
	@echo "make clean-all  - Remove venv and all build artifacts"
	@echo ""
	@echo "Quick start: make install && make dev"

# Create virtual environment
$(VENV)/bin/activate:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV)
	@echo "✓ Virtual environment created"

# Install dependencies in editable mode
install: $(VENV)/bin/activate
	@echo "Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	@echo ""
	@echo "✓ Installation complete!"
	@echo "Run 'make dev' to start the Dagster webserver"

# Start Dagster development server
# This combines both webserver and daemon (like running airflow webserver + scheduler)
dev:
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Starting Dagster webserver..."
	@echo "Access the UI at: http://localhost:3000"
	@echo ""
	$(VENV)/bin/dagster dev -m ingestion_sample

# Run tests
test:
	$(VENV)/bin/pytest tests/

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned build artifacts"

# Clean everything including venv
clean-all: clean
	rm -rf $(VENV)
	@echo "✓ Removed virtual environment"
