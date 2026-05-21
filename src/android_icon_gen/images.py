"""Image loading, resizing, color, and composition helpers."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import cast

from PIL import Image, ImageChops, ImageDraw, ImageOps

from android_icon_gen.specs import (
    ADAPTIVE_SAFE_ZONE_FRACTION,
    LEGACY_SAFE_ZONE_FRACTION,
    PLAY_STORE_ICON_SIZE,
)

Color = tuple[int, int, int, int]
TRANSPARENT: Color = (0, 0, 0, 0)
WHITE: Color = (255, 255, 255, 255)
RESAMPLE = Image.Resampling.LANCZOS


def load_rgba_image(path: Path) -> Image.Image:
    """Load an image as EXIF-corrected RGBA."""

    source = path.expanduser()
    if not source.is_file():
        msg = f"Image file does not exist: {source}"
        raise FileNotFoundError(msg)

    with Image.open(source) as image:
        fixed = ImageOps.exif_transpose(image)
        rgba = fixed.convert("RGBA")
        rgba.load()
        return rgba


def parse_hex_color(value: str | None) -> Color | None:
    """Parse #RGB, #RRGGBB, or #RRGGBBAA into an RGBA tuple."""

    if value is None:
        return None

    raw = value.strip()
    if not raw:
        return None
    if raw.startswith("#"):
        raw = raw[1:]

    if len(raw) == 3:
        raw = "".join(char * 2 for char in raw)

    if len(raw) not in {6, 8}:
        msg = "Background color must be #RGB, #RRGGBB, or #RRGGBBAA."
        raise ValueError(msg)

    try:
        red = int(raw[0:2], 16)
        green = int(raw[2:4], 16)
        blue = int(raw[4:6], 16)
        alpha = int(raw[6:8], 16) if len(raw) == 8 else 255
    except ValueError as exc:
        msg = "Background color contains non-hexadecimal characters."
        raise ValueError(msg) from exc

    return red, green, blue, alpha


def color_to_hex(color: Color) -> str:
    """Return an opaque color as #RRGGBB for user-facing warnings."""

    red, green, blue, _alpha = color
    return f"#{red:02x}{green:02x}{blue:02x}"


def has_transparency(image: Image.Image) -> bool:
    """Return true when an image contains transparent or translucent pixels."""

    alpha_min, alpha_max = cast(tuple[int, int], image.getchannel("A").getextrema())
    return alpha_min < 255 or alpha_max < 255


def is_monochrome_like(image: Image.Image) -> bool:
    """Estimate whether visible pixels are already effectively monochrome."""

    sample = image.copy()
    sample.thumbnail((64, 64), RESAMPLE)
    visible = 0
    monochrome = 0

    for red, green, blue, alpha in _iter_rgba_pixels(sample):
        if alpha <= 16:
            continue
        visible += 1
        if max(red, green, blue) - min(red, green, blue) <= 12:
            monochrome += 1

    return visible > 0 and monochrome / visible > 0.92


def average_edge_color(image: Image.Image) -> Color:
    """Pick a stable background color from visible edge pixels."""

    sample = image.copy()
    sample.thumbnail((64, 64), RESAMPLE)
    width, height = sample.size
    red_total = 0
    green_total = 0
    blue_total = 0
    count = 0

    for x in range(width):
        for y in (0, height - 1):
            red, green, blue, alpha = cast(tuple[int, int, int, int], sample.getpixel((x, y)))
            if alpha > 32:
                red_total += red
                green_total += green
                blue_total += blue
                count += 1

    for y in range(1, max(height - 1, 1)):
        for x in (0, width - 1):
            red, green, blue, alpha = cast(tuple[int, int, int, int], sample.getpixel((x, y)))
            if alpha > 32:
                red_total += red
                green_total += green
                blue_total += blue
                count += 1

    if count == 0:
        return WHITE

    return red_total // count, green_total // count, blue_total // count, 255


def _iter_rgba_pixels(image: Image.Image) -> Iterable[tuple[int, int, int, int]]:
    data = image.get_flattened_data() if hasattr(image, "get_flattened_data") else image.getdata()
    return cast(Iterable[tuple[int, int, int, int]], data)


def resize_to_fit(
    image: Image.Image,
    size: int,
    *,
    fill: Color = TRANSPARENT,
    fraction: float = 1.0,
) -> Image.Image:
    """Fit an image inside a square canvas without cropping."""

    canvas = Image.new("RGBA", (size, size), fill)
    max_content_size = max(1, round(size * fraction))
    resized = image.copy()
    resized.thumbnail((max_content_size, max_content_size), RESAMPLE)
    x = (size - resized.width) // 2
    y = (size - resized.height) // 2
    canvas.alpha_composite(resized, (x, y))
    return canvas


def resize_to_cover(image: Image.Image, size: int) -> Image.Image:
    """Resize and center-crop an image to fill a square canvas."""

    width, height = image.size
    scale = max(size / width, size / height)
    resized_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    resized = image.resize(resized_size, RESAMPLE)
    left = (resized.width - size) // 2
    top = (resized.height - size) // 2
    return resized.crop((left, top, left + size, top + size)).convert("RGBA")


def flatten_over_color(image: Image.Image, color: Color) -> Image.Image:
    """Composite a transparent image over a flat color."""

    background = Image.new("RGBA", image.size, color)
    return Image.alpha_composite(background, image)


def make_foreground_layer(
    image: Image.Image,
    size: int,
    *,
    explicit_layer: bool,
) -> Image.Image:
    """Create an adaptive foreground layer."""

    fraction = 1.0 if explicit_layer else ADAPTIVE_SAFE_ZONE_FRACTION
    return resize_to_fit(image, size, fraction=fraction)


def make_background_layer(
    image: Image.Image | None,
    size: int,
    *,
    background_color: Color,
) -> Image.Image:
    """Create an adaptive background layer."""

    if image is None:
        return Image.new("RGBA", (size, size), background_color)

    covered = resize_to_cover(image, size)
    if has_transparency(covered):
        return flatten_over_color(covered, background_color)
    return covered


def make_monochrome_layer(
    image: Image.Image,
    size: int,
    *,
    explicit_layer: bool,
) -> Image.Image:
    """Create a white monochrome layer whose alpha carries the icon shape."""

    fraction = 1.0 if explicit_layer else ADAPTIVE_SAFE_ZONE_FRACTION
    fitted = resize_to_fit(image, size, fraction=fraction)
    gray = ImageOps.grayscale(fitted)
    alpha = fitted.getchannel("A")
    mono_alpha = ImageChops.multiply(gray, alpha)
    result = Image.new("RGBA", (size, size), TRANSPARENT)
    result.putalpha(mono_alpha)
    return result


def make_legacy_icon(
    source: Image.Image,
    size: int,
    *,
    background_color: Color,
    foreground: Image.Image | None = None,
    background: Image.Image | None = None,
) -> Image.Image:
    """Create a pre-adaptive Android launcher icon."""

    if foreground is not None or background is not None:
        background_layer = make_background_layer(
            background, size, background_color=background_color
        )
        foreground_layer = resize_to_fit(
            foreground or source,
            size,
            fraction=1.0 if foreground is not None else LEGACY_SAFE_ZONE_FRACTION,
        )
        return Image.alpha_composite(background_layer, foreground_layer)

    if has_transparency(source):
        fitted = resize_to_fit(source, size, fraction=LEGACY_SAFE_ZONE_FRACTION)
        return flatten_over_color(fitted, background_color)

    return resize_to_cover(source, size)


def make_round_icon(icon: Image.Image) -> Image.Image:
    """Apply a circular mask for legacy round launcher icons."""

    size = min(icon.size)
    square = resize_to_cover(icon, size)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size - 1, size - 1), fill=255)

    alpha = ImageChops.multiply(square.getchannel("A"), mask)
    result = square.copy()
    result.putalpha(alpha)
    return result


def make_play_store_icon(source: Image.Image, *, background_color: Color) -> Image.Image:
    """Create a 512x512 Play Store icon."""

    if has_transparency(source):
        fitted = resize_to_fit(
            source,
            PLAY_STORE_ICON_SIZE,
            fill=background_color,
            fraction=LEGACY_SAFE_ZONE_FRACTION,
        )
        return flatten_over_color(fitted, background_color)

    return resize_to_cover(source, PLAY_STORE_ICON_SIZE)
