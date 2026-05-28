# Contributing to Capsule

Thank you for your interest in contributing! The open-source parts of Capsule — the Python SDK (`packages/sdk/`) and the Rust replay engine (`packages/replay-engine/`) — welcome community contributions.

## What's Open Source

| Package | License | Contributions Welcome |
|---------|---------|----------------------|
| `packages/sdk/` | Apache 2.0 | ✅ Yes |
| `packages/replay-engine/` | Apache 2.0 | ✅ Yes |
| `packages/cloud-api/` | Proprietary | ❌ No |
| `packages/cloud-web/` | Proprietary | ❌ No |

## Getting Started

### Prerequisites

- Python 3.11+
- Rust 1.75+ (for the replay engine)
- Node.js 20+ (for docs tooling)

### Setup

```bash
git clone https://github.com/capsule-dev/capsule.git
cd capsule

# Set up the Python SDK
cd packages/sdk
python -m venv .venv
source .venv/bin/activate       # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Set up the Rust replay engine
cd ../replay-engine
cargo build
```

### Verify Setup

```bash
# Python tests
cd packages/sdk
pytest tests/

# Rust tests
cd packages/replay-engine
cargo test

# Type checking
cd packages/sdk
mypy --strict src/
```

## Development Workflow

1. **Fork** the repository and create a branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** following the code style guides below

3. **Write tests** — all new code requires tests with > 80% coverage

4. **Run the full CI check locally:**
   ```bash
   pre-commit run --all-files
   pytest tests/ --cov=capsule --cov-fail-under=80
   mypy --strict src/
   ```

5. **Submit a PR** with:
   - A clear title following [Conventional Commits](https://www.conventionalcommits.org/)
   - A description explaining what, why, and how to test
   - Screenshots for any UI changes

## Code Style

### Python

- Formatter: `ruff format`
- Linter: `ruff check`
- Type checker: `mypy --strict`
- Line length: 100 characters
- All public functions must have type hints
- No bare `except:` — always specify exception types
- Google-style docstrings

### Rust

- Formatter: `cargo fmt`
- Linter: `cargo clippy -- -D warnings`
- No `unwrap()` in production code paths (tests are OK)
- All public items must have doc comments

## Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`

Examples:
```
feat(sdk): add automatic capture for Anthropic SDK
fix(replay): fix cassette lookup for tool call responses
docs(spec): clarify memory snapshot format
```

## Pull Request Requirements

- Title follows Conventional Commits format
- Description includes: what changed, why, how to test
- All CI checks pass
- Tests written for new code
- No new linting warnings
- No new security vulnerabilities (`pip-audit`, `cargo audit`)
- Linked to an issue (if fixing a bug or implementing a tracked feature)

## Reporting Issues

Use GitHub Issues with the appropriate template:
- **Bug report** — for reproducible bugs
- **Feature request** — for new functionality proposals
- **Format RFC** — for proposed changes to the `.capsule` file format

**For security vulnerabilities, see [SECURITY.md](SECURITY.md).**

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
