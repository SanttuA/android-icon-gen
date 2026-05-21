from __future__ import annotations

from pathlib import Path

from android_icon_gen.gui import (
    GuiFormState,
    background_color_display,
    build_config_from_state,
    output_target_from_display,
)
from android_icon_gen.models import OutputTarget


def test_build_config_from_gui_state_maps_blank_optional_fields() -> None:
    state = GuiFormState(
        source="icon.png",
        output_dir="out",
        icon_name="",
        foreground="",
        background="background.png",
        monochrome="",
        background_color="",
        output_target="Expo",
        create_zip=True,
        include_play_icon=False,
    )

    config = build_config_from_state(state)

    assert config.source == Path("icon.png")
    assert config.output_dir == Path("out")
    assert config.icon_name == "ic_launcher"
    assert config.foreground is None
    assert config.background == Path("background.png")
    assert config.monochrome is None
    assert config.background_color is None
    assert config.output_target is OutputTarget.EXPO
    assert config.create_zip is True
    assert config.include_play_icon is False


def test_background_color_display_marks_blank_as_auto() -> None:
    display = background_color_display("")

    assert display.text == "Auto"
    assert display.color is None
    assert display.valid is True


def test_background_color_display_normalizes_valid_hex_for_swatch() -> None:
    assert background_color_display("#abc").color == "#aabbcc"
    assert background_color_display("#11223344").color == "#112233"


def test_background_color_display_marks_invalid_values() -> None:
    display = background_color_display("not-a-color")

    assert display.text == "Invalid"
    assert display.color is None
    assert display.valid is False


def test_output_target_from_display_accepts_labels_and_raw_values() -> None:
    assert output_target_from_display("Android") is OutputTarget.ANDROID
    assert output_target_from_display("Android + Expo") is OutputTarget.BOTH
    assert output_target_from_display("expo") is OutputTarget.EXPO
