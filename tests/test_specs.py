from __future__ import annotations

import pytest

from android_icon_gen.specs import (
    ADAPTIVE_LAYER_SIZES,
    LEGACY_LAUNCHER_SIZES,
    generated_asset_specs,
    validate_resource_name,
)


def test_android_density_sizes_are_expected() -> None:
    assert LEGACY_LAUNCHER_SIZES == {
        "mdpi": 48,
        "hdpi": 72,
        "xhdpi": 96,
        "xxhdpi": 144,
        "xxxhdpi": 192,
    }
    assert ADAPTIVE_LAYER_SIZES["xxxhdpi"] == 432


def test_generated_asset_specs_include_xml_layers_and_play_icon() -> None:
    specs = generated_asset_specs("ic_test")
    paths = {spec.path.as_posix() for spec in specs}

    assert "res/mipmap-anydpi-v26/ic_test.xml" in paths
    assert "res/mipmap-anydpi-v26/ic_test_round.xml" in paths
    assert "res/mipmap-xxxhdpi/ic_test_foreground.png" in paths
    assert "res/mipmap-xxxhdpi/ic_test_background.png" in paths
    assert "res/mipmap-xxxhdpi/ic_test_monochrome.png" in paths
    assert "play_store_icon.png" in paths


def test_validate_resource_name_rejects_invalid_names() -> None:
    assert validate_resource_name("ic_launcher") == "ic_launcher"

    with pytest.raises(ValueError):
        validate_resource_name("Icon")

    with pytest.raises(ValueError):
        validate_resource_name("1_icon")
