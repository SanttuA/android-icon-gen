from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

from PIL import Image, ImageDraw

from android_icon_gen.generator import generate_icons
from android_icon_gen.models import GenerationConfig, OutputTarget


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


def test_generate_icons_writes_expo_pack_and_zip(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    image = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((160, 160, 864, 864), radius=96, fill=(25, 120, 220, 255))
    image.save(source)
    output_dir = tmp_path / "generated"

    result = generate_icons(
        GenerationConfig(
            source=source,
            output_dir=output_dir,
            background_color="#10182080",
            output_target=OutputTarget.EXPO,
        )
    )

    asset_dir = output_dir / "expo/assets/images"
    assert (asset_dir / "icon.png").is_file()
    assert (asset_dir / "adaptive-icon.png").is_file()
    assert (asset_dir / "adaptive-icon-background.png").is_file()
    assert (asset_dir / "monochrome-icon.png").is_file()
    assert (asset_dir / "splash-icon.png").is_file()
    assert (asset_dir / "favicon.png").is_file()
    assert (output_dir / "expo/app.json.snippet").is_file()
    assert not (output_dir / "res").exists()
    assert not (output_dir / "play_store_icon.png").exists()
    assert result.zip_path == output_dir / "expo-icons.zip"
    assert result.zip_path.is_file()

    with Image.open(asset_dir / "icon.png") as icon:
        assert icon.size == (1024, 1024)
        assert icon.getchannel("A").getextrema() == (255, 255)
    with Image.open(asset_dir / "favicon.png") as favicon:
        assert favicon.size == (48, 48)

    snippet = json.loads((output_dir / "expo/app.json.snippet").read_text(encoding="utf-8"))
    expo_config = snippet["expo"]
    assert expo_config["icon"] == "./assets/images/icon.png"
    assert expo_config["android"]["icon"] == "./assets/images/icon.png"
    assert expo_config["android"]["adaptiveIcon"] == {
        "foregroundImage": "./assets/images/adaptive-icon.png",
        "backgroundImage": "./assets/images/adaptive-icon-background.png",
        "backgroundColor": "#101820",
        "monochromeImage": "./assets/images/monochrome-icon.png",
    }
    assert expo_config["web"]["favicon"] == "./assets/images/favicon.png"
    assert expo_config["plugins"][0][0] == "expo-splash-screen"
    assert expo_config["plugins"][0][1]["backgroundColor"] == "#101820"

    with ZipFile(result.zip_path) as archive:
        names = set(archive.namelist())
    assert "expo/assets/images/icon.png" in names
    assert "expo/app.json.snippet" in names


def test_generate_icons_can_write_android_and_expo_outputs(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGBA", (1024, 1024), (0, 128, 255, 255)).save(source)
    output_dir = tmp_path / "generated"

    result = generate_icons(
        GenerationConfig(
            source=source,
            output_dir=output_dir,
            icon_name="ic_both",
            background_color="#ffffff",
            output_target=OutputTarget.BOTH,
        )
    )

    assert (output_dir / "res/mipmap-anydpi-v26/ic_both.xml").is_file()
    assert (output_dir / "expo/assets/images/icon.png").is_file()
    assert result.zip_path == output_dir / "icons.zip"

    with ZipFile(result.zip_path) as archive:
        names = set(archive.namelist())
    assert "res/mipmap-anydpi-v26/ic_both.xml" in names
    assert "expo/assets/images/icon.png" in names
