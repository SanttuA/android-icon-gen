# AGENTS.md

## Project Overview
Android Icon Gen is a uv-managed Python 3.14 desktop and CLI app. It generates Android launcher
icons, adaptive icon layers, optional themed monochrome resources, and a 512x512 Google Play icon
from user-supplied images.

## Development Commands
- Install dependencies: `uv sync`
- Run the GUI: `uv run android-icon-gen gui`
- Run the CLI: `uv run android-icon-gen generate path/to/icon.png --output output`
- Format: `uv run ruff format .`
- Lint: `uv run ruff check .`
- Type check: `uv run mypy src tests`
- Test: `uv run pytest`

## Package And Security Policy
- Use uv for dependency management and locking.
- Keep `.python-version` at Python 3.14 unless the project intentionally changes runtime support.
- Runtime dependencies should stay minimal; Pillow is currently the only runtime dependency.
- The project uses `[tool.uv] exclude-newer = "24 hours"` to avoid resolving packages uploaded in
  the last 24 hours.
- Do not add dependencies without a clear reason and corresponding tests.

## Code Structure
- `android_icon_gen.specs`: Android density sizes, output names, and resource validation.
- `android_icon_gen.images`: image loading, resizing, composition, colors, and warnings.
- `android_icon_gen.generator`: orchestration for producing files.
- `android_icon_gen.writer`: resource XML and PNG writing.
- `android_icon_gen.archive`: zip packaging.
- `android_icon_gen.cli`: command-line entry point.
- `android_icon_gen.gui`: Tkinter desktop app.

## Engineering Guidelines
- Keep files focused and small; move shared behavior into modules before a file becomes hard to
  scan.
- Prefer pure functions in the image and resource pipeline so behavior remains easy to test.
- Validate Android resource names before writing files.
- Preserve transparency where possible, and surface warnings instead of silently producing poor
  adaptive/themed icon results.
- Keep GUI code thin; business logic belongs in the generator library.

## GitHub And CI
- Pull requests against `main` run Ruff format check, Ruff lint, mypy, and pytest through GitHub
  Actions.
- Do not commit generated output folders, local virtual environments, or cache directories.
- Keep README usage examples aligned with the CLI arguments.
