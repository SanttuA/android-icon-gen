"""Command-line interface for Android Icon Gen."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from android_icon_gen.generator import generate_icons
from android_icon_gen.gui import launch_gui
from android_icon_gen.models import GenerationConfig, OutputTarget
from android_icon_gen.specs import DEFAULT_ICON_NAME


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "gui":
        launch_gui()
        return 0
    if args.command == "generate":
        return _run_generate(args)

    parser.print_help()
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""

    parser = argparse.ArgumentParser(
        prog="android-icon-gen",
        description="Generate Android launcher and Play Store icons.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("gui", help="open the desktop app")

    generate_parser = subparsers.add_parser("generate", help="generate icons from an image")
    generate_parser.add_argument("source", type=Path, help="source image path")
    generate_parser.add_argument("--output", required=True, type=Path, help="output directory")
    generate_parser.add_argument(
        "--target",
        choices=[target.value for target in OutputTarget],
        default=OutputTarget.ANDROID.value,
        help="output target: android resources, Expo assets, or both",
    )
    generate_parser.add_argument(
        "--name", default=DEFAULT_ICON_NAME, help="Android icon resource name"
    )
    generate_parser.add_argument(
        "--foreground", type=Path, help="optional adaptive foreground image"
    )
    generate_parser.add_argument(
        "--background", type=Path, help="optional adaptive background image"
    )
    generate_parser.add_argument("--monochrome", type=Path, help="optional themed monochrome image")
    generate_parser.add_argument(
        "--background-color",
        help="background color as #RGB, #RRGGBB, or #RRGGBBAA",
    )
    generate_parser.add_argument(
        "--zip",
        dest="create_zip",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="write android-icons.zip, enabled by default",
    )
    generate_parser.add_argument(
        "--play-icon",
        dest="include_play_icon",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="write play_store_icon.png, enabled by default",
    )

    return parser


def _run_generate(args: argparse.Namespace) -> int:
    config = GenerationConfig(
        source=args.source,
        output_dir=args.output,
        icon_name=args.name,
        foreground=args.foreground,
        background=args.background,
        monochrome=args.monochrome,
        background_color=args.background_color,
        create_zip=args.create_zip,
        include_play_icon=args.include_play_icon,
        output_target=OutputTarget(args.target),
    )

    try:
        result = generate_icons(config)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Generated {len(result.files)} files in {result.output_dir}")
    if result.zip_path is not None:
        print(f"Archive: {result.zip_path}")
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)

    return 0
