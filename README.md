# Android Icon Gen

Android Icon Gen is a Python 3.14 desktop and CLI app for creating Android launcher icons from a
user-provided image. It generates legacy launcher PNGs, adaptive icon layers, Android resource XML,
a 512x512 Google Play icon, and an optional zip archive.

## Requirements

- Python 3.14
- uv

## Setup

```bash
uv sync
```

## Desktop App

```bash
uv run android-icon-gen gui
```

The desktop app lets you choose a source image, optional adaptive icon layer overrides, an icon
resource name, a background color, and an output folder. Background color can be chosen with the
picker, typed as `#RGB`, `#RRGGBB`, or `#RRGGBBAA`, or left blank to auto-pick from image edges.

## CLI

```bash
uv run android-icon-gen generate assets/app-icon.png --output output
```

Useful options:

```bash
uv run android-icon-gen generate assets/app-icon.png \
  --output output \
  --name ic_launcher \
  --foreground assets/foreground.png \
  --background assets/background.png \
  --monochrome assets/monochrome.png \
  --background-color "#0f172a" \
  --zip
```

Disable specific default outputs:

```bash
uv run android-icon-gen generate assets/app-icon.png --output output --no-play-icon --no-zip
```

## Generated Output

By default the generator writes:

- `res/mipmap-anydpi-v26/ic_launcher.xml`
- `res/mipmap-anydpi-v26/ic_launcher_round.xml`
- legacy density launcher PNGs in `res/mipmap-mdpi` through `res/mipmap-xxxhdpi`
- adaptive foreground, background, and monochrome PNG resources
- `play_store_icon.png`
- `android-icons.zip`

Copy the generated `res/` directory into your Android app module, then reference the icons from
your manifest:

```xml
<application
    android:icon="@mipmap/ic_launcher"
    android:roundIcon="@mipmap/ic_launcher_round">
</application>
```

## Development

```bash
uv run ruff format .
uv run ruff check .
uv run mypy src tests
uv run pytest
```

Dependencies are resolved with uv's `exclude-newer = "24 hours"` policy to avoid packages uploaded
within the last 24 hours.
