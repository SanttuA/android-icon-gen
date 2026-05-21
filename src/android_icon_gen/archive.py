"""Zip archive support."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from android_icon_gen.specs import ZIP_NAME


def create_zip_archive(
    output_dir: Path, files: tuple[Path, ...], archive_name: str = ZIP_NAME
) -> Path:
    """Create a zip archive containing generated files."""

    zip_path = output_dir / archive_name
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
        for file_path in sorted(files):
            archive.write(file_path, file_path.relative_to(output_dir).as_posix())

    return zip_path
