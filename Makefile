.PHONY: up down build seed test lint demo clean logs

# ─── Docker ───────────────────────────────────────────────────────────────────

up: ## Start all services
	docker compose up --build -d

down: ## Stop all services
	docker compose down

build: ## Build all images without starting
	docker compose build

logs: ## Tail logs for all services
	docker compose logs -f

# ─── Database ─────────────────────────────────────────────────────────────────

migrate: ## Run Alembic migrations
	docker compose exec backend alembic upgrade head

seed: ## Seed demo data (users, assets, threat intel)
	docker compose exec backend python -m scripts.seed_demo_data

# ─── Testing ──────────────────────────────────────────────────────────────────

test: test-backend test-contracts test-frontend ## Run all test suites

test-backend: ## Run backend tests with coverage
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing

test-contracts: ## Run Foundry contract tests
	cd contracts && forge test -vvv

test-frontend: ## Run frontend Vitest tests
	cd frontend && npm run test

# ─── Linting & Type Checking ─────────────────────────────────────────────────

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint and type-check backend
	cd backend && ruff check . && ruff format --check . && mypy --strict app/

lint-frontend: ## Lint and type-check frontend
	cd frontend && npx eslint src/ && npx tsc --noEmit

format: ## Auto-format all code
	cd backend && ruff format .
	cd frontend && npx prettier --write src/

# ─── Demo ─────────────────────────────────────────────────────────────────────

demo: up seed ## Start services and seed demo data
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║  SentinelChain is running!                                  ║"
	@echo "║                                                              ║"
	@echo "║  Dashboard:  http://localhost:5173                           ║"
	@echo "║  API Docs:   http://localhost:8000/docs                      ║"
	@echo "║  MinIO:      http://localhost:9001                           ║"
	@echo "║                                                              ║"
	@echo "║  Demo logins:                                                ║"
	@echo "║    admin   / admin_demo_password                             ║"
	@echo "║    analyst / analyst_demo_password                           ║"
	@echo "║    viewer  / viewer_demo_password                            ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"

# ─── Cleanup ──────────────────────────────────────────────────────────────────

clean: down ## Stop services and remove volumes
	docker compose down -v
	rm -rf pgdata/ redis_data/ minio_data/

# ─── Help ─────────────────────────────────────────────────────────────────────

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
