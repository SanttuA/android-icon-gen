"""Expo asset specifications and config snippets."""

from __future__ import annotations

import json
from pathlib import PurePosixPath
from typing import Any

EXPO_DIRECTORY = PurePosixPath("expo")
EXPO_ASSET_DIRECTORY = EXPO_DIRECTORY / "assets" / "images"
EXPO_SNIPPET_PATH = EXPO_DIRECTORY / "app.json.snippet"

EXPO_ICON_SIZE = 1024
EXPO_FAVICON_SIZE = 48

EXPO_ICON_NAME = "icon.png"
EXPO_ADAPTIVE_ICON_NAME = "adaptive-icon.png"
EXPO_ADAPTIVE_BACKGROUND_NAME = "adaptive-icon-background.png"
EXPO_MONOCHROME_ICON_NAME = "monochrome-icon.png"
EXPO_SPLASH_ICON_NAME = "splash-icon.png"
EXPO_FAVICON_NAME = "favicon.png"

EXPO_ICON_CONFIG_PATH = "./assets/images/icon.png"
EXPO_ADAPTIVE_ICON_CONFIG_PATH = "./assets/images/adaptive-icon.png"
EXPO_ADAPTIVE_BACKGROUND_CONFIG_PATH = "./assets/images/adaptive-icon-background.png"
EXPO_MONOCHROME_ICON_CONFIG_PATH = "./assets/images/monochrome-icon.png"
EXPO_SPLASH_ICON_CONFIG_PATH = "./assets/images/splash-icon.png"
EXPO_FAVICON_CONFIG_PATH = "./assets/images/favicon.png"


def expo_asset_path(file_name: str) -> PurePosixPath:
    """Return the output path for an Expo image asset."""

    return EXPO_ASSET_DIRECTORY / file_name


def expo_app_json_snippet(background_color: str) -> str:
    """Build an app.json snippet for generated Expo assets."""

    config: dict[str, Any] = {
        "expo": {
            "icon": EXPO_ICON_CONFIG_PATH,
            "android": {
                "icon": EXPO_ICON_CONFIG_PATH,
                "adaptiveIcon": {
                    "foregroundImage": EXPO_ADAPTIVE_ICON_CONFIG_PATH,
                    "backgroundImage": EXPO_ADAPTIVE_BACKGROUND_CONFIG_PATH,
                    "backgroundColor": background_color,
                    "monochromeImage": EXPO_MONOCHROME_ICON_CONFIG_PATH,
                },
            },
            "web": {
                "favicon": EXPO_FAVICON_CONFIG_PATH,
            },
            "plugins": [
                [
                    "expo-splash-screen",
                    {
                        "backgroundColor": background_color,
                        "image": EXPO_SPLASH_ICON_CONFIG_PATH,
                        "imageWidth": 200,
                    },
                ],
            ],
        },
    }
    return json.dumps(config, indent=2) + "\n"
