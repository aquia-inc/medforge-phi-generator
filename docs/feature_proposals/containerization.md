# Containerization — Design Document

> **Status:** Draft — not yet implemented
> **Author:** MedForge team
> **Last updated:** 2026-04-09
> **Related:** [MSG Format Support](msg-format-support.md) — these decisions share Docker infrastructure and should be made together
> **Location:** `docs/feature_proposals/`

## Problem Statement

MedForge requires Python 3.13 and the `uv` package manager on the host machine. While `uv.lock` guarantees deterministic dependency resolution, the tool still depends on the user having the correct Python version installed. Containerization would eliminate this requirement and provide a reproducible runtime across macOS, Linux, and Windows.

Additionally, the planned MSG format converter (see `msg-format-support.md`) requires a .NET runtime via Docker. If MedForge itself is containerized, both tools can share Docker infrastructure through `docker-compose`.

## Current State

- **Python:** 3.13+ required (`requires-python = ">=3.13"` in pyproject.toml)
- **Package manager:** `uv` with `uv.lock` (208KB, 25 runtime dependencies)
- **Entry point:** `python -m src.cli <command>` (or `./medforge` bash wrapper that activates `.venv`)
- **Templates:** `cust_templates/` directory (43 files, ~16MB) — read-only at runtime
- **Output:** `output/{run_name}/{phi_positive,phi_negative,metadata}/` — user-specified directory
- **Optional:** `ANTHROPIC_API_KEY` env var for LLM enrichment (tool works without it)
- **No existing:** Dockerfile, Makefile, docker-compose.yml

## Recommendation: Support Both Docker and Native

**Docker should be optional. Native (`uv sync`) remains the primary path.**

Rationale:
1. The tool's audience is developers who likely have Python. `uv` installs in one command and `uv.lock` guarantees determinism.
2. Docker Desktop is not universally available on government machines (CMS IT policies may restrict it).
3. Docker adds real value for CI/CD pipelines, users without Python, and future MSG converter integration.
4. A Makefile wrapping Docker commands gives ergonomic parity for both paths.

## Tradeoffs

| Docker | Native (`uv sync`) |
|--------|-------------------|
| Zero Python/uv setup on host | Faster startup (~1-2s Docker overhead per invocation) |
| Reproducible across macOS/Linux/Windows | No Docker Desktop requirement (gov't machines) |
| Prepares for MSG converter compose integration | Direct filesystem access, no volume mount complexity |
| Isolates 25 Python deps from host | Shell globbing works naturally in paths |
| ~500MB image (cached after first build) | Rich terminal output works without `-t` flag |
| Volume mount required for output directory | `--parallel-workers` has no CPU limit concerns |

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Docker not available on target machines | Medium | Keep native path primary; Docker is opt-in |
| Output file ownership on Linux | Low | Makefile uses `--user $(id -u):$(id -g)` |
| API key baked into image layers | High | `.dockerignore` excludes `.env`; inject via `-e` flag at runtime |
| Rich terminal formatting lost | Low | Makefile adds `-t` flag for TTY allocation |
| Image size (~500MB) | Low | Acceptable for dev CLI tool; cached after first build |
| `cust_templates` path resolution | Low | `WORKDIR /app` matches the `./cust_templates` relative path used in `cli.py:148` and `cli.py:714` |

## Implementation Sketch

### Dockerfile

Single-stage build using the official uv Docker image (`ghcr.io/astral-sh/uv:python3.13-bookworm-slim`). Based on [astral-sh/uv-docker-example](https://github.com/astral-sh/uv-docker-example) best practices.

**Why single-stage (not multi-stage)?** The build toolchain is just `uv` (~30MB). The runtime dependencies (reportlab, pikepdf, openpyxl, python-docx, etc.) must exist in the final image regardless. Multi-stage would save ~30MB by removing `uv` from the final image — not worth the added complexity.

**Key design choices:**
- **Two-phase dependency install** — deps first (`--no-install-project`), then source. Changes to `src/` don't invalidate the ~300MB dependency layer.
- **BuildKit cache mounts** — `--mount=type=cache,target=/root/.cache/uv` persists download cache across builds.
- **`--frozen` flag** — asserts lockfile matches pyproject.toml; fails the build if they diverge.
- **Non-root user** — `medforge` user (UID 1000) for container security.
- **`cust_templates/` baked in** — read-only, ships with repo. Not volume-mounted (eliminates a failure mode).
- **No `.env` in image** — excluded by `.dockerignore`; API key injected at runtime.

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Phase 1: Install dependencies only (cached unless pyproject.toml/uv.lock change)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Phase 2: Copy source and install project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Non-root user
RUN groupadd --system --gid 1000 medforge \
    && useradd --system --gid 1000 --uid 1000 --create-home medforge \
    && mkdir -p /app/output && chown medforge:medforge /app/output

ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT []
USER medforge

CMD ["python", "-m", "src.cli", "--help"]
```

### .dockerignore

Security-critical — prevents `.env` (contains API key) from being baked into image layers.

```
.git/
.venv/
output/
.env
.env.*
__pycache__/
*.py[cod]
tests/
docs/
_archive/
.claude/
.pytest_cache/
.ruff_cache/
.DS_Store
medforge_Claude.md
*.log
*.tmp
```

### Makefile

Wraps both Docker and native commands. `ARGS` variable enables pass-through of CLI flags.

| Target | Command | Description |
|--------|---------|-------------|
| `docker-build` | `docker build -t medforge .` | Build the Docker image |
| `docker-generate` | `docker run --rm -t -v ./output:/app/output -e ANTHROPIC_API_KEY medforge python -m src.cli generate $(ARGS)` | Generate documents in container |
| `docker-validate` | `docker run --rm -t -v ./output:/app/output medforge python -m src.cli validate $(ARGS)` | Validate output |
| `docker-stats` | `docker run --rm -t -v ./output:/app/output medforge python -m src.cli stats $(ARGS)` | Show stats |
| `docker-shell` | `docker run --rm -it -v ./output:/app/output -e ANTHROPIC_API_KEY medforge /bin/bash` | Debug shell |
| `docker-test` | `docker run --rm medforge python -m pytest tests/ -v` | Run tests in container |
| `docker-clean` | `docker rmi medforge` | Remove image |
| `generate` | `uv run python -m src.cli generate $(ARGS)` | Native generation |
| `validate` | `uv run python -m src.cli validate $(ARGS)` | Native validation |
| `test` | `uv run pytest` | Native tests |
| `lint` | `uv run ruff check` | Native linting |
| `setup` | `uv sync` | Install dependencies natively |
| `help` | Print all targets | Self-documenting |

**Usage examples:**
```bash
# Docker path
make docker-build
make docker-generate ARGS="--phi-positive 100 --phi-negative 300"
make docker-generate ARGS="--cui-positive 70 --cui-all --llm-percentage 0"

# Native path
make setup
make generate ARGS="--count 200 --llm-percentage 0.2"
```

### docker-compose.yml (future integration with MSG converter)

Prepares for the MSG converter described in `msg-format-support.md`:

```yaml
services:
  medforge:
    build: .
    volumes:
      - ./output:/app/output
    environment:
      - ANTHROPIC_API_KEY

  # Future: MSG converter from msg-format-support.md
  # eml2msg:
  #   build: ./tools/eml2msg
  #   volumes:
  #     - ./output:/data
  #   network_mode: none
  #   profiles: ["msg"]
```

When the MSG converter is implemented, the workflow becomes:
```bash
docker compose run medforge python -m src.cli generate --count 200
docker compose run --profile msg eml2msg /data/production_run_*/
```

## Code Changes Required

No source code changes needed — only new files:

| File | Status | Notes |
|------|--------|-------|
| `src/cli.py:148,714` | No change | `./cust_templates` resolves correctly with `WORKDIR /app` |
| `src/generators/llm_generator.py:16` | No change | `load_dotenv()` silently skips when no `.env` file present |
| `.dockerignore` | New | Security-critical |
| `Dockerfile` | New | Single-stage uv build |
| `Makefile` | New | Docker + native targets |
| `docker-compose.yml` | New | MSG converter placeholder |
| `README.md` | Edit | Add Docker section |

## Level of Effort

| Phase | LOE | Description |
|-------|-----|-------------|
| `.dockerignore` + `Dockerfile` | 0.5 day | Security file + build definition |
| `Makefile` | 0.5 day | Docker and native targets |
| `docker-compose.yml` | 0.25 day | Minimal with MSG placeholder |
| README + testing | 0.25 day | Document both paths, smoke test |
| **Total** | **~1.5 days** | |

## Decision Record

- **Decided:** Document options for future implementation
- **Recommended:** Both Docker and native paths; Docker optional, native primary
- **Related to:** `msg-format-support.md` — both use Docker; implement together when needed
- **Deferred because:** Native path works for current team; Docker value increases when MSG converter is built
- **Trigger to implement:** When the MSG converter is prioritized, or when a new team member hits Python/uv setup issues
