"""High-level icon generation orchestration."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from PIL import Image

from android_icon_gen.archive import create_zip_archive
from android_icon_gen.expo import (
    EXPO_ADAPTIVE_BACKGROUND_NAME,
    EXPO_ADAPTIVE_ICON_NAME,
    EXPO_FAVICON_NAME,
    EXPO_ICON_NAME,
    EXPO_ICON_SIZE,
    EXPO_MONOCHROME_ICON_NAME,
    EXPO_SNIPPET_PATH,
    EXPO_SPLASH_ICON_NAME,
    expo_app_json_snippet,
    expo_asset_path,
)
from android_icon_gen.images import (
    Color,
    average_edge_color,
    color_to_hex,
    has_transparency,
    is_monochrome_like,
    load_rgba_image,
    make_background_layer,
    make_expo_adaptive_foreground,
    make_expo_app_icon,
    make_expo_favicon,
    make_expo_splash_icon,
    make_foreground_layer,
    make_legacy_icon,
    make_monochrome_layer,
    make_play_store_icon,
    make_round_icon,
    opaque_color,
    parse_hex_color,
)
from android_icon_gen.models import GenerationConfig, GenerationResult, OutputTarget
from android_icon_gen.specs import (
    ADAPTIVE_LAYER_SIZES,
    COMBINED_ZIP_NAME,
    DENSITY_ORDER,
    EXPO_ZIP_NAME,
    LEGACY_LAUNCHER_SIZES,
    PLAY_STORE_ICON_SIZE,
    ZIP_NAME,
    adaptive_xml_directory,
    density_directory,
    validate_resource_name,
)
from android_icon_gen.writer import adaptive_icon_xml, write_png, write_text


def generate_icons(config: GenerationConfig) -> GenerationResult:
    """Generate icon resources from a source image."""

    output_target = OutputTarget(config.output_target)
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
        output_target=output_target,
    )

    files: list[Path] = []
    if _target_includes_android(output_target):
        files.extend(
            _generate_android_files(
                output_dir=output_dir,
                icon_name=validate_resource_name(config.icon_name),
                source=source,
                foreground=foreground,
                background=background,
                monochrome=monochrome,
                background_color=background_color,
                include_play_icon=config.include_play_icon,
            )
        )
    if _target_includes_expo(output_target):
        files.extend(
            _generate_expo_files(
                output_dir=output_dir,
                source=source,
                foreground=foreground,
                background=background,
                monochrome=monochrome,
                background_color=background_color,
            )
        )

    zip_path = (
        create_zip_archive(output_dir, tuple(files), archive_name=_archive_name(output_target))
        if config.create_zip
        else None
    )

    return GenerationResult(
        output_dir=output_dir,
        files=tuple(files),
        warnings=tuple(warnings),
        zip_path=zip_path,
    )


def _generate_android_files(
    *,
    output_dir: Path,
    icon_name: str,
    source: Image.Image,
    foreground: Image.Image | None,
    background: Image.Image | None,
    monochrome: Image.Image | None,
    background_color: Color,
    include_play_icon: bool,
) -> list[Path]:
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

    if include_play_icon:
        play_store_icon = make_play_store_icon(source, background_color=background_color)
        files.append(write_png(output_dir / "play_store_icon.png", play_store_icon))

    return files


def _generate_expo_files(
    *,
    output_dir: Path,
    source: Image.Image,
    foreground: Image.Image | None,
    background: Image.Image | None,
    monochrome: Image.Image | None,
    background_color: Color,
) -> list[Path]:
    expo_background_color = opaque_color(background_color)
    foreground_source = foreground or source
    monochrome_source = monochrome or foreground or source

    files = [
        write_png(
            _output_path(output_dir, expo_asset_path(EXPO_ICON_NAME)),
            make_expo_app_icon(
                source,
                background_color=expo_background_color,
                foreground=foreground,
                background=background,
            ),
        ),
        write_png(
            _output_path(output_dir, expo_asset_path(EXPO_ADAPTIVE_ICON_NAME)),
            make_expo_adaptive_foreground(
                foreground_source,
                explicit_layer=foreground is not None,
            ),
        ),
        write_png(
            _output_path(output_dir, expo_asset_path(EXPO_ADAPTIVE_BACKGROUND_NAME)),
            make_background_layer(
                background,
                EXPO_ICON_SIZE,
                background_color=expo_background_color,
            ),
        ),
        write_png(
            _output_path(output_dir, expo_asset_path(EXPO_MONOCHROME_ICON_NAME)),
            make_monochrome_layer(
                monochrome_source,
                EXPO_ICON_SIZE,
                explicit_layer=monochrome is not None,
            ),
        ),
        write_png(
            _output_path(output_dir, expo_asset_path(EXPO_SPLASH_ICON_NAME)),
            make_expo_splash_icon(foreground_source),
        ),
        write_png(
            _output_path(output_dir, expo_asset_path(EXPO_FAVICON_NAME)),
            make_expo_favicon(foreground_source),
        ),
        write_text(
            _output_path(output_dir, EXPO_SNIPPET_PATH),
            expo_app_json_snippet(color_to_hex(expo_background_color)),
        ),
    ]

    return files


def _output_path(output_dir: Path, relative_path: PurePosixPath) -> Path:
    return output_dir.joinpath(*relative_path.parts)


def _target_includes_android(output_target: OutputTarget) -> bool:
    return output_target in {OutputTarget.ANDROID, OutputTarget.BOTH}


def _target_includes_expo(output_target: OutputTarget) -> bool:
    return output_target in {OutputTarget.EXPO, OutputTarget.BOTH}


def _archive_name(output_target: OutputTarget) -> str:
    if output_target is OutputTarget.EXPO:
        return EXPO_ZIP_NAME
    if output_target is OutputTarget.BOTH:
        return COMBINED_ZIP_NAME
    return ZIP_NAME


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
    output_target: OutputTarget,
) -> list[str]:
    warnings: list[str] = []

    width, height = source.size
    if width != height:
        warnings.append(
            "Source image is not square; generated icons were centered and cropped or padded."
        )
    recommended_size = (
        EXPO_ICON_SIZE if _target_includes_expo(output_target) else PLAY_STORE_ICON_SIZE
    )
    if min(width, height) < recommended_size:
        warnings.append(
            f"Source image is smaller than {recommended_size}px on one side; "
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
