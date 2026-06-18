# Changelog

All notable changes to Capsule SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

<!-- Add new releases above this line -->

## [0.1.1] - 2026-06

### Added
- `login`, `logout`, `upload` CLI commands
- `load_config()` / `save_config()` shared helpers
- `capsule-trace` entry point

### Fixed
- OpenAI integration step-recording (descriptor + MagicMock bugs)

## [0.1.0] - 2026-05

### Added
- Initial release
- `@capsule.trace` decorator
- OpenAI and Anthropic integrations
- Cassette-based deterministic replay
- Branch from any step
- `.capsule` file export/import
- LangChain and LangGraph integrations
- Full CLI
