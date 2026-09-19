# Contributing to SentinelChain

Thank you for your interest in contributing to **SentinelChain**! This document provides instructions for setting up your development environment, adhering to code style guidelines, running tests, and opening pull requests.

---

## 1. Development Setup

### Prerequisites
* **Python**: `3.12+`
* **Node.js**: `20+` & `npm 10+`
* **Foundry**: `forge` (for Solidity smart contracts)
* **Docker & Docker Compose** (optional for full containerized stack)

### Backend Setup
```bash
cd backend
python -m venv .venv
# Linux / macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

pip install -e ".[dev]"
```

### Frontend Setup
```bash
cd frontend
npm install
```

### Smart Contracts Setup
```bash
cd contracts
forge install foundry-rs/forge-std --no-commit
forge build
```

---

## 2. Code Quality & Standards

Every change must pass static analysis and unit test suites cleanly before submission.

### Backend Validation
```bash
cd backend
# 1. Linting
python -m ruff check app/

# 2. Code formatting check
python -m ruff format --check app/

# 3. Static type analysis
python -m mypy app/

# 4. Pytest test suite with coverage
python -m pytest tests/ -v --cov=app
```

### Frontend Validation
```bash
cd frontend
# 1. ESLint
npx eslint src/

# 2. TypeScript type check
npx tsc --noEmit

# 3. Vitest unit tests
npm run test
```

### Smart Contract Validation
```bash
cd contracts
forge test -vvv
```

---

## 3. Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

* `feat(scope): add new feature`
* `fix(scope): resolve bug or edge-case`
* `docs(scope): update documentation or diagrams`
* `refactor(scope): optimize internal logic without changing behavior`
* `test(scope): add or improve test coverage`
* `ci(scope): update GitHub Actions or deployment scripts`

---

## 4. Pull Request Checklist

Before submitting your PR, ensure:
- [ ] All 7 GitHub Actions CI jobs pass green.
- [ ] New services and algorithms include unit tests ($\ge 85\%$ coverage on core domain logic).
- [ ] Architecture diagrams and documentation in `docs/` or `README.md` are updated.
- [ ] No secrets, `.env` files, or binary artifacts are committed.
