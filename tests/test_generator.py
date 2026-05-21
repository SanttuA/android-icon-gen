from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from PIL import Image, ImageDraw

from android_icon_gen.generator import generate_icons
from android_icon_gen.models import GenerationConfig


def test_generate_icons_writes_android_resources_and_zip(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    image = Image.new("RGBA", (640, 480), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((160, 80, 480, 400), fill=(25, 120, 220, 255))
    image.save(source)
    output_dir = tmp_path / "generated"

    result = generate_icons(
        GenerationConfig(
            source=source,
            output_dir=output_dir,
            icon_name="ic_test",
            background_color="#101820",
        )
    )

    assert (output_dir / "res/mipmap-anydpi-v26/ic_test.xml").is_file()
    assert (output_dir / "res/mipmap-anydpi-v26/ic_test_round.xml").is_file()
    assert (output_dir / "res/mipmap-xxxhdpi/ic_test.png").is_file()
    assert (output_dir / "res/mipmap-xxxhdpi/ic_test_round.png").is_file()
    assert (output_dir / "res/mipmap-xxxhdpi/ic_test_foreground.png").is_file()
    assert (output_dir / "res/mipmap-xxxhdpi/ic_test_background.png").is_file()
    assert (output_dir / "res/mipmap-xxxhdpi/ic_test_monochrome.png").is_file()
    assert (output_dir / "play_store_icon.png").is_file()
    assert result.zip_path == output_dir / "android-icons.zip"
    assert result.zip_path.is_file()

    with Image.open(output_dir / "res/mipmap-xxxhdpi/ic_test_foreground.png") as foreground:
        assert foreground.size == (432, 432)

    with Image.open(output_dir / "play_store_icon.png") as play_icon:
        assert play_icon.size == (512, 512)

    with ZipFile(result.zip_path) as archive:
        names = set(archive.namelist())
    assert "res/mipmap-anydpi-v26/ic_test.xml" in names
    assert "play_store_icon.png" in names


def test_generate_icons_can_skip_zip_and_play_icon(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGBA", (256, 256), (255, 0, 0, 255)).save(source)
    output_dir = tmp_path / "generated"

    result = generate_icons(
        GenerationConfig(
            source=source,
            output_dir=output_dir,
            create_zip=False,
            include_play_icon=False,
        )
    )

    assert result.zip_path is None
    assert not (output_dir / "android-icons.zip").exists()
    assert not (output_dir / "play_store_icon.png").exists()
    assert result.warnings
