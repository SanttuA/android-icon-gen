from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from android_icon_gen.cli import main


def test_cli_generate_writes_resources(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "source.png"
    output_dir = tmp_path / "generated"
    Image.new("RGBA", (512, 512), (0, 128, 255, 255)).save(source)

    exit_code = main(
        [
            "generate",
            str(source),
            "--output",
            str(output_dir),
            "--name",
            "ic_cli",
            "--no-zip",
            "--no-play-icon",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Generated" in captured.out
    assert (output_dir / "res/mipmap-mdpi/ic_cli.png").is_file()
    assert not (output_dir / "android-icons.zip").exists()


def test_cli_returns_error_for_invalid_resource_name(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "source.png"
    Image.new("RGBA", (512, 512), (0, 128, 255, 255)).save(source)

    exit_code = main(["generate", str(source), "--output", str(tmp_path / "out"), "--name", "Bad"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Android resource names" in captured.err
