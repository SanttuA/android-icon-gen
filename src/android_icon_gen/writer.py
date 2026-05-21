"""File writers for Android resources."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from android_icon_gen.specs import ANDROID_XML_NAMESPACE


def write_png(path: Path, image: Image.Image) -> Path:
    """Write a PNG image, creating parent directories as needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)
    return path


def adaptive_icon_xml(icon_name: str, *, include_monochrome: bool = True) -> str:
    """Build Android adaptive icon XML."""

    lines = [
        f'<adaptive-icon xmlns:android="{ANDROID_XML_NAMESPACE}">',
        f'    <background android:drawable="@mipmap/{icon_name}_background" />',
        f'    <foreground android:drawable="@mipmap/{icon_name}_foreground" />',
    ]
    if include_monochrome:
        lines.append(f'    <monochrome android:drawable="@mipmap/{icon_name}_monochrome" />')
    lines.append("</adaptive-icon>")
    return "\n".join(lines) + "\n"


def write_text(path: Path, content: str) -> Path:
    """Write a UTF-8 text file, creating parent directories as needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
