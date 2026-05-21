"""Shared data models for icon generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from android_icon_gen.specs import DEFAULT_ICON_NAME


@dataclass(frozen=True, slots=True)
class GenerationConfig:
    """User-provided generation settings."""

    source: Path
    output_dir: Path
    icon_name: str = DEFAULT_ICON_NAME
    foreground: Path | None = None
    background: Path | None = None
    monochrome: Path | None = None
    background_color: str | None = None
    create_zip: bool = True
    include_play_icon: bool = True


@dataclass(frozen=True, slots=True)
class GenerationResult:
    """Summary of generated files."""

    output_dir: Path
    files: tuple[Path, ...]
    warnings: tuple[str, ...]
    zip_path: Path | None = None
