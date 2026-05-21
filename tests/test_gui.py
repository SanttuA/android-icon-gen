from __future__ import annotations

from pathlib import Path

from android_icon_gen.gui import GuiFormState, build_config_from_state


def test_build_config_from_gui_state_maps_blank_optional_fields() -> None:
    state = GuiFormState(
        source="icon.png",
        output_dir="out",
        icon_name="",
        foreground="",
        background="background.png",
        monochrome="",
        background_color="",
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
    assert config.create_zip is True
    assert config.include_play_icon is False
