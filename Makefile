.PHONY: install dev test clean clean-all help check-venv windows-guide

VENV := venv

ifeq ($(OS),Windows_NT)
PYTHON_BOOTSTRAP := py -3
VENV_PYTHON := $(VENV)/Scripts/python.exe
VENV_PIP := $(VENV)/Scripts/pip.exe
VENV_DAGSTER := $(VENV)/Scripts/dagster.exe
VENV_PYTEST := $(VENV)/Scripts/pytest.exe
else
PYTHON_BOOTSTRAP := python3
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
VENV_DAGSTER := $(VENV)/bin/dagster
VENV_PYTEST := $(VENV)/bin/pytest
endif

PYTHON := $(VENV_PYTHON)
PIP := $(VENV_PIP)
DAGSTER := $(VENV_DAGSTER)
PYTEST := $(VENV_PYTEST)

# Default target
help:
	@echo "Dagster Demo - Available Commands"
	@echo "=================================="
	@echo "make install    - Create venv and install dependencies"
	@echo "make dev        - Start Dagster webserver (like 'airflow webserver')"
	@echo "make test       - Run tests"
	@echo "make clean      - Remove build artifacts and cache files"
	@echo "make clean-all  - Remove venv and all build artifacts"
	@echo "make windows-guide - Print Windows setup/run notes"
	@echo ""
	@echo "Quick start: make install && make dev"

# Create virtual environment
$(PYTHON):
	@echo "Creating virtual environment..."
	$(PYTHON_BOOTSTRAP) -m venv $(VENV)
	@echo "✓ Virtual environment created"

# Install dependencies in editable mode
install: $(PYTHON)
	@echo "Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	@echo ""
	@echo "✓ Installation complete!"
	@echo "Run 'make dev' to start the Dagster webserver"

# Start Dagster development server
# This combines both webserver and daemon (like running airflow webserver + scheduler)
# Loads both code locations: ingestion_pipelines and data_marts
check-venv:
	@$(PYTHON_BOOTSTRAP) -c "import pathlib,sys; p=pathlib.Path(r'$(PYTHON)'); print(\"Virtual environment not found. Run 'make install' first.\") if not p.exists() else None; sys.exit(0 if p.exists() else 1)"

dev: check-venv
	@echo "Starting Dagster webserver with multiple code locations..."
	@echo "  - ingestion_pipelines (data ingestion)"
	@echo "  - data_marts (analytics aggregations)"
	@echo ""
	@echo "Access the UI at: http://localhost:3000"
	@echo ""
	$(DAGSTER) dev -w workspace.yaml

# Run tests
test: check-venv
	$(PYTEST) tests/

# Clean build artifacts
clean:
	$(PYTHON_BOOTSTRAP) -c "from pathlib import Path; import shutil; [shutil.rmtree(p, ignore_errors=True) for p in Path('.').rglob('__pycache__') if p.is_dir()]; [shutil.rmtree(p, ignore_errors=True) for p in Path('.').rglob('*.egg-info') if p.is_dir()]; [shutil.rmtree(p, ignore_errors=True) for p in Path('.').rglob('.pytest_cache') if p.is_dir()]; [p.unlink(missing_ok=True) for p in Path('.').rglob('*.pyc') if p.is_file()]"
	@echo "✓ Cleaned build artifacts"

# Clean everything including venv
clean-all: clean
	$(PYTHON_BOOTSTRAP) -c "from pathlib import Path; import shutil; shutil.rmtree(Path('$(VENV)'), ignore_errors=True)"
	@echo "✓ Removed virtual environment"

# Windows notes for users cloning this repo
windows-guide:
	@echo "Windows setup:"
	@echo "1) Install Python 3.10+ and check 'Add python.exe to PATH'"
	@echo "2) Install GNU Make (via Chocolatey: choco install make, or use Git Bash)"
	@echo "3) Run: make install"
	@echo "4) Run: make dev"
	@echo "5) Open: http://localhost:3000"
