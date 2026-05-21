from __future__ import annotations

from pathlib import Path
from typing import cast

from PIL import Image

from android_icon_gen.images import (
    has_transparency,
    load_rgba_image,
    make_expo_adaptive_foreground,
    make_expo_app_icon,
    make_expo_favicon,
    make_monochrome_layer,
    make_round_icon,
    parse_hex_color,
)


def test_parse_hex_color_accepts_common_formats() -> None:
    assert parse_hex_color("#abc") == (170, 187, 204, 255)
    assert parse_hex_color("#112233") == (17, 34, 51, 255)
    assert parse_hex_color("#11223344") == (17, 34, 51, 68)
    assert parse_hex_color("") is None


def test_load_rgba_image_converts_mode(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    Image.new("RGB", (32, 24), (10, 20, 30)).save(source)

    loaded = load_rgba_image(source)

    assert loaded.mode == "RGBA"
    assert loaded.size == (32, 24)


def test_round_icon_masks_corners() -> None:
    source = Image.new("RGBA", (64, 64), (255, 0, 0, 255))

    rounded = make_round_icon(source)

    assert cast(tuple[int, int, int, int], rounded.getpixel((0, 0)))[3] == 0
    assert cast(tuple[int, int, int, int], rounded.getpixel((32, 32)))[3] == 255
    assert has_transparency(rounded)


def test_monochrome_layer_preserves_shape_alpha() -> None:
    source = Image.new("RGBA", (64, 64), (255, 255, 255, 0))
    source.putpixel((32, 32), (255, 255, 255, 255))

    monochrome = make_monochrome_layer(source, 64, explicit_layer=True)

    assert cast(tuple[int, int, int, int], monochrome.getpixel((0, 0)))[3] == 0
    assert cast(tuple[int, int, int, int], monochrome.getpixel((32, 32)))[3] == 255


def test_expo_app_icon_is_opaque() -> None:
    source = Image.new("RGBA", (128, 128), (255, 255, 255, 0))
    source.putpixel((64, 64), (255, 0, 0, 255))

    icon = make_expo_app_icon(source, background_color=(10, 20, 30, 64))

    assert icon.size == (1024, 1024)
    assert icon.getchannel("A").getextrema() == (255, 255)


def test_expo_adaptive_foreground_keeps_transparent_safe_zone() -> None:
    source = Image.new("RGBA", (128, 128), (255, 0, 0, 255))

    foreground = make_expo_adaptive_foreground(source, explicit_layer=False)

    assert foreground.size == (1024, 1024)
    assert cast(tuple[int, int, int, int], foreground.getpixel((0, 0)))[3] == 0


def test_expo_favicon_is_48_px() -> None:
    source = Image.new("RGBA", (128, 128), (255, 0, 0, 255))

    favicon = make_expo_favicon(source)

    assert favicon.size == (48, 48)
