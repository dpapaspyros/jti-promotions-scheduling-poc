PYTHON = backend/.venv/Scripts/python.exe
UV     = backend/.venv/Scripts/uv.exe

# ── Backend ────────────────────────────────────────────────────────────────────

.PHONY: be-install
be-install:  ## Install backend dependencies via uv
	$(UV) pip install django djangorestframework django-cors-headers djangorestframework-simplejwt flake8 isort black

.PHONY: be-run
be-run:  ## Start Django dev server on :8000
	cd backend && ../$(PYTHON) manage.py runserver

.PHONY: be-migrate
be-migrate:  ## Apply Django migrations
	cd backend && ../$(PYTHON) manage.py migrate

.PHONY: be-makemigrations
be-makemigrations:  ## Create new Django migrations
	cd backend && ../$(PYTHON) manage.py makemigrations

.PHONY: be-createsuperuser
be-createsuperuser:  ## Create a Django admin superuser
	cd backend && ../$(PYTHON) manage.py createsuperuser

.PHONY: be-loaddata
be-loaddata:  ## Load initial fixture data (promoters, POS, test admin)
	cd backend && ../$(PYTHON) manage.py loaddata scheduling/fixtures/initial_data.json

.PHONY: be-install
be-install:  ## Install backend dependencies via uv
	$(UV) pip install django djangorestframework django-cors-headers djangorestframework-simplejwt flake8 isort black openpyxl

.PHONY: be-lint
be-lint:  ## Run black + isort + flake8
	cd backend && ../$(PYTHON) -m black .
	cd backend && ../$(PYTHON) -m isort .
	cd backend && ../$(PYTHON) -m flake8 .

.PHONY: be-lint-check
be-lint-check:  ## Check formatting without making changes (CI mode)
	cd backend && ../$(PYTHON) -m black --check .
	cd backend && ../$(PYTHON) -m isort --check-only .
	cd backend && ../$(PYTHON) -m flake8 .

# ── Frontend ───────────────────────────────────────────────────────────────────

.PHONY: fe-install
fe-install:  ## Install frontend dependencies
	cd frontend && npm install

.PHONY: fe-run
fe-run:  ## Start Vite dev server on :5173
	cd frontend && npm run dev

.PHONY: fe-build
fe-build:  ## Build frontend for production
	cd frontend && npm run build

.PHONY: fe-lint
fe-lint:  ## Run ESLint
	cd frontend && npm run lint

# ── Combined ───────────────────────────────────────────────────────────────────

.PHONY: install
install: be-install fe-install  ## Install all dependencies

.PHONY: lint
lint: be-lint-check fe-lint  ## Run all linters (CI mode)

.PHONY: help
help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
