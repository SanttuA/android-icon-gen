"""High-level Android icon generation orchestration."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from android_icon_gen.archive import create_zip_archive
from android_icon_gen.images import (
    Color,
    average_edge_color,
    color_to_hex,
    has_transparency,
    is_monochrome_like,
    load_rgba_image,
    make_background_layer,
    make_foreground_layer,
    make_legacy_icon,
    make_monochrome_layer,
    make_play_store_icon,
    make_round_icon,
    parse_hex_color,
)
from android_icon_gen.models import GenerationConfig, GenerationResult
from android_icon_gen.specs import (
    ADAPTIVE_LAYER_SIZES,
    DENSITY_ORDER,
    LEGACY_LAUNCHER_SIZES,
    PLAY_STORE_ICON_SIZE,
    adaptive_xml_directory,
    density_directory,
    validate_resource_name,
)
from android_icon_gen.writer import adaptive_icon_xml, write_png, write_text


def generate_icons(config: GenerationConfig) -> GenerationResult:
    """Generate Android icon resources from a source image."""

    icon_name = validate_resource_name(config.icon_name)
    output_dir = config.output_dir.expanduser().resolve()
    source = load_rgba_image(config.source)
    foreground = load_rgba_image(config.foreground) if config.foreground else None
    background = load_rgba_image(config.background) if config.background else None
    monochrome = load_rgba_image(config.monochrome) if config.monochrome else None

    background_color = _resolve_background_color(config.background_color, background or source)
    warnings = _build_warnings(
        source=source,
        foreground=foreground,
        background=background,
        monochrome=monochrome,
        requested_background_color=config.background_color,
        resolved_background_color=background_color,
    )

    files: list[Path] = []
    for density in DENSITY_ORDER:
        density_dir = output_dir / "res" / density_directory(density)
        legacy_size = LEGACY_LAUNCHER_SIZES[density]
        adaptive_size = ADAPTIVE_LAYER_SIZES[density]

        legacy_icon = make_legacy_icon(
            source,
            legacy_size,
            background_color=background_color,
            foreground=foreground,
            background=background,
        )
        files.append(write_png(density_dir / f"{icon_name}.png", legacy_icon))
        files.append(
            write_png(density_dir / f"{icon_name}_round.png", make_round_icon(legacy_icon))
        )

        foreground_layer = make_foreground_layer(
            foreground or source,
            adaptive_size,
            explicit_layer=foreground is not None,
        )
        background_layer = make_background_layer(
            background,
            adaptive_size,
            background_color=background_color,
        )
        monochrome_layer = make_monochrome_layer(
            monochrome or foreground or source,
            adaptive_size,
            explicit_layer=monochrome is not None,
        )

        files.append(write_png(density_dir / f"{icon_name}_foreground.png", foreground_layer))
        files.append(write_png(density_dir / f"{icon_name}_background.png", background_layer))
        files.append(write_png(density_dir / f"{icon_name}_monochrome.png", monochrome_layer))

    xml_dir = output_dir / "res" / adaptive_xml_directory()
    xml = adaptive_icon_xml(icon_name)
    files.append(write_text(xml_dir / f"{icon_name}.xml", xml))
    files.append(write_text(xml_dir / f"{icon_name}_round.xml", xml))

    if config.include_play_icon:
        play_store_icon = make_play_store_icon(source, background_color=background_color)
        files.append(write_png(output_dir / "play_store_icon.png", play_store_icon))

    zip_path = create_zip_archive(output_dir, tuple(files)) if config.create_zip else None

    return GenerationResult(
        output_dir=output_dir,
        files=tuple(files),
        warnings=tuple(warnings),
        zip_path=zip_path,
    )


def _resolve_background_color(requested: str | None, image: Image.Image) -> Color:
    parsed = parse_hex_color(requested)
    if parsed is not None:
        return parsed
    return average_edge_color(image)


def _build_warnings(
    *,
    source: Image.Image,
    foreground: Image.Image | None,
    background: Image.Image | None,
    monochrome: Image.Image | None,
    requested_background_color: str | None,
    resolved_background_color: Color,
) -> list[str]:
    warnings: list[str] = []

    width, height = source.size
    if width != height:
        warnings.append(
            "Source image is not square; generated icons were centered and cropped or padded."
        )
    if min(width, height) < PLAY_STORE_ICON_SIZE:
        warnings.append(
            f"Source image is smaller than {PLAY_STORE_ICON_SIZE}px on one side; "
            "large outputs may look soft."
        )

    if foreground is None or background is None:
        warnings.append(
            "Adaptive icon layers were derived from the available image data; separate foreground "
            "and background images usually produce better Android adaptive icons."
        )
    if foreground is None and not has_transparency(source):
        warnings.append(
            "The source image has no transparency; a transparent foreground image improves masked "
            "launcher and themed icon results."
        )
    if monochrome is None and not is_monochrome_like(foreground or source):
        warnings.append(
            "The monochrome themed icon was generated automatically; provide a dedicated "
            "monochrome image for best Android 13 themed icon results."
        )
    if background is None and requested_background_color is None:
        warnings.append(
            f"Background color was auto-picked as {color_to_hex(resolved_background_color)}."
        )

    return warnings
