"""Android icon resource specifications."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

ANDROID_XML_NAMESPACE = "http://schemas.android.com/apk/res/android"
DEFAULT_ICON_NAME = "ic_launcher"
ZIP_NAME = "android-icons.zip"
EXPO_ZIP_NAME = "expo-icons.zip"
COMBINED_ZIP_NAME = "icons.zip"

DENSITY_ORDER = ("mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi")

LEGACY_LAUNCHER_SIZES: dict[str, int] = {
    "mdpi": 48,
    "hdpi": 72,
    "xhdpi": 96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}

ADAPTIVE_LAYER_SIZES: dict[str, int] = {
    "mdpi": 108,
    "hdpi": 162,
    "xhdpi": 216,
    "xxhdpi": 324,
    "xxxhdpi": 432,
}

PLAY_STORE_ICON_SIZE = 512
ADAPTIVE_SAFE_ZONE_FRACTION = 72 / 108
LEGACY_SAFE_ZONE_FRACTION = 0.82

RESOURCE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True, slots=True)
class AssetSpec:
    """A generated Android asset path and expected size."""

    path: PurePosixPath
    size_px: int | None
    description: str


def validate_resource_name(name: str) -> str:
    """Validate and normalize an Android resource filename stem."""

    normalized = name.strip()
    if not RESOURCE_NAME_PATTERN.fullmatch(normalized):
        msg = (
            "Android resource names must start with a lowercase letter and contain only "
            "lowercase letters, numbers, and underscores."
        )
        raise ValueError(msg)
    return normalized


def density_directory(density: str) -> str:
    """Return the mipmap resource directory for a density."""

    if density not in DENSITY_ORDER:
        msg = f"Unknown Android density: {density}"
        raise ValueError(msg)
    return f"mipmap-{density}"


def adaptive_xml_directory() -> str:
    """Return the adaptive icon XML resource directory."""

    return "mipmap-anydpi-v26"


def generated_asset_specs(icon_name: str, include_play_icon: bool = True) -> tuple[AssetSpec, ...]:
    """Return the planned generated asset paths for an icon name."""

    name = validate_resource_name(icon_name)
    specs: list[AssetSpec] = []

    for density in DENSITY_ORDER:
        directory = PurePosixPath("res") / density_directory(density)
        legacy_size = LEGACY_LAUNCHER_SIZES[density]
        layer_size = ADAPTIVE_LAYER_SIZES[density]

        specs.extend(
            (
                AssetSpec(directory / f"{name}.png", legacy_size, "legacy launcher icon"),
                AssetSpec(directory / f"{name}_round.png", legacy_size, "legacy round icon"),
                AssetSpec(
                    directory / f"{name}_foreground.png",
                    layer_size,
                    "adaptive foreground layer",
                ),
                AssetSpec(
                    directory / f"{name}_background.png",
                    layer_size,
                    "adaptive background layer",
                ),
                AssetSpec(
                    directory / f"{name}_monochrome.png",
                    layer_size,
                    "adaptive monochrome layer",
                ),
            )
        )

    xml_directory = PurePosixPath("res") / adaptive_xml_directory()
    specs.extend(
        (
            AssetSpec(xml_directory / f"{name}.xml", None, "adaptive icon XML"),
            AssetSpec(xml_directory / f"{name}_round.xml", None, "round adaptive icon XML"),
        )
    )

    if include_play_icon:
        specs.append(
            AssetSpec(
                PurePosixPath("play_store_icon.png"),
                PLAY_STORE_ICON_SIZE,
                "Google Play icon",
            )
        )

    return tuple(specs)
