"""Tkinter desktop interface."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import ImageTk

from android_icon_gen.generator import generate_icons
from android_icon_gen.images import (
    average_edge_color,
    load_rgba_image,
    make_legacy_icon,
    make_round_icon,
    parse_hex_color,
)
from android_icon_gen.models import GenerationConfig
from android_icon_gen.specs import DEFAULT_ICON_NAME


@dataclass(frozen=True, slots=True)
class GuiFormState:
    """Raw GUI form values."""

    source: str
    output_dir: str
    icon_name: str
    foreground: str
    background: str
    monochrome: str
    background_color: str
    create_zip: bool
    include_play_icon: bool


def build_config_from_state(state: GuiFormState) -> GenerationConfig:
    """Build a generation config from GUI form state."""

    return GenerationConfig(
        source=Path(state.source),
        output_dir=Path(state.output_dir),
        icon_name=state.icon_name.strip() or DEFAULT_ICON_NAME,
        foreground=_optional_path(state.foreground),
        background=_optional_path(state.background),
        monochrome=_optional_path(state.monochrome),
        background_color=state.background_color.strip() or None,
        create_zip=state.create_zip,
        include_play_icon=state.include_play_icon,
    )


def launch_gui() -> None:
    """Start the Tkinter app."""

    root = tk.Tk()
    IconGeneratorApp(root)
    root.mainloop()


def _optional_path(value: str) -> Path | None:
    stripped = value.strip()
    return Path(stripped) if stripped else None


class IconGeneratorApp:
    """Desktop app controller and view."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Android Icon Gen")
        self.root.minsize(760, 560)

        self.source_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(Path.cwd() / "output"))
        self.icon_name_var = tk.StringVar(value=DEFAULT_ICON_NAME)
        self.foreground_var = tk.StringVar()
        self.background_var = tk.StringVar()
        self.monochrome_var = tk.StringVar()
        self.background_color_var = tk.StringVar()
        self.zip_var = tk.BooleanVar(value=True)
        self.play_icon_var = tk.BooleanVar(value=True)
        self._preview_images: list[object] = []

        self._build()
        self.source_var.trace_add("write", self._on_preview_input_changed)
        self.background_color_var.trace_add("write", self._on_preview_input_changed)

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=16)
        outer.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=0)
        outer.rowconfigure(2, weight=1)

        form = ttk.Frame(outer)
        form.grid(row=0, column=0, columnspan=2, sticky="ew")
        form.columnconfigure(1, weight=1)

        self._path_row(form, 0, "Source image", self.source_var, self._choose_source)
        self._path_row(form, 1, "Output folder", self.output_var, self._choose_output_dir)
        self._entry_row(form, 2, "Icon name", self.icon_name_var)
        self._entry_row(form, 3, "Background color", self.background_color_var)

        advanced = ttk.LabelFrame(outer, text="Adaptive layer overrides", padding=12)
        advanced.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 12))
        advanced.columnconfigure(1, weight=1)
        self._path_row(advanced, 0, "Foreground", self.foreground_var, self._choose_foreground)
        self._path_row(advanced, 1, "Background", self.background_var, self._choose_background)
        self._path_row(advanced, 2, "Monochrome", self.monochrome_var, self._choose_monochrome)

        preview_frame = ttk.LabelFrame(outer, text="Preview", padding=12)
        preview_frame.grid(row=2, column=0, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.columnconfigure(1, weight=1)
        self.square_preview = ttk.Label(preview_frame, text="Square", anchor="center")
        self.round_preview = ttk.Label(preview_frame, text="Round", anchor="center")
        self.square_preview.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.round_preview.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        warnings_frame = ttk.LabelFrame(outer, text="Validation", padding=12)
        warnings_frame.grid(row=2, column=1, sticky="nsew", padx=(12, 0))
        warnings_frame.rowconfigure(0, weight=1)
        warnings_frame.columnconfigure(0, weight=1)
        self.warning_text = tk.Text(
            warnings_frame, width=34, height=12, wrap="word", state="disabled"
        )
        self.warning_text.grid(row=0, column=0, sticky="nsew")

        actions = ttk.Frame(outer)
        actions.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        actions.columnconfigure(0, weight=1)
        ttk.Checkbutton(actions, text="Create zip", variable=self.zip_var).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Checkbutton(actions, text="Play icon", variable=self.play_icon_var).grid(
            row=0,
            column=1,
            sticky="w",
            padx=(12, 0),
        )
        ttk.Button(actions, text="Generate", command=self._generate).grid(
            row=0, column=2, sticky="e"
        )

    def _path_row(
        self,
        parent: tk.Misc,
        row: int,
        label: str,
        variable: tk.StringVar,
        command: Callable[[], None],
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=(8, 8))
        ttk.Button(parent, text="Browse", command=command).grid(row=row, column=2, sticky="e")

    def _entry_row(self, parent: tk.Misc, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variable).grid(
            row=row,
            column=1,
            columnspan=2,
            sticky="ew",
            padx=(8, 0),
        )

    def _choose_source(self) -> None:
        self._choose_file(self.source_var)

    def _choose_foreground(self) -> None:
        self._choose_file(self.foreground_var)

    def _choose_background(self) -> None:
        self._choose_file(self.background_var)

    def _choose_monochrome(self) -> None:
        self._choose_file(self.monochrome_var)

    def _choose_file(self, variable: tk.StringVar) -> None:
        path = filedialog.askopenfilename(
            title="Choose image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp"),
                ("All files", "*.*"),
            ],
        )
        if path:
            variable.set(path)
            self._update_preview()

    def _choose_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Choose output folder")
        if path:
            self.output_var.set(path)

    def _on_preview_input_changed(self, *_args: object) -> None:
        self._update_preview()

    def _state(self) -> GuiFormState:
        return GuiFormState(
            source=self.source_var.get(),
            output_dir=self.output_var.get(),
            icon_name=self.icon_name_var.get(),
            foreground=self.foreground_var.get(),
            background=self.background_var.get(),
            monochrome=self.monochrome_var.get(),
            background_color=self.background_color_var.get(),
            create_zip=self.zip_var.get(),
            include_play_icon=self.play_icon_var.get(),
        )

    def _generate(self) -> None:
        try:
            result = generate_icons(build_config_from_state(self._state()))
        except Exception as exc:
            messagebox.showerror("Generation failed", str(exc))
            return

        self._set_warnings(result.warnings)
        archive_line = f"\nArchive: {result.zip_path}" if result.zip_path else ""
        messagebox.showinfo(
            "Generation complete",
            f"Generated {len(result.files)} files in {result.output_dir}{archive_line}",
        )

    def _update_preview(self) -> None:
        source_path = self.source_var.get().strip()
        if not source_path:
            self._set_preview_text("Square", "Round")
            self._set_warnings(())
            return

        try:
            source = load_rgba_image(Path(source_path))
            color = parse_hex_color(self.background_color_var.get()) or average_edge_color(source)
            square = make_legacy_icon(source, 128, background_color=color)
            rounded = make_round_icon(square)
            square_photo = ImageTk.PhotoImage(square)
            round_photo = ImageTk.PhotoImage(rounded)
        except Exception as exc:
            self._set_preview_text("Preview unavailable", "Preview unavailable")
            self._set_warnings((str(exc),))
            return

        self._preview_images = [square_photo, round_photo]
        self.square_preview.configure(image=square_photo, text="")
        self.round_preview.configure(image=round_photo, text="")
        self._set_warnings(())

    def _set_preview_text(self, square: str, rounded: str) -> None:
        self._preview_images = []
        self.square_preview.configure(image="", text=square)
        self.round_preview.configure(image="", text=rounded)

    def _set_warnings(self, warnings: tuple[str, ...]) -> None:
        self.warning_text.configure(state="normal")
        self.warning_text.delete("1.0", "end")
        self.warning_text.insert(
            "1.0", "\n\n".join(warnings) if warnings else "No issues detected."
        )
        self.warning_text.configure(state="disabled")
