"""Script to compile the Typst banner into a PNG image."""

from pathlib import Path

import rich
import typst

LOGO_PATH = Path("docs/logo")
FONTS_PATH = Path("docs/fonts")

if __name__ == "__main__":
    # Define paths relative to the project root
    input_typ_file = LOGO_PATH / "banner.typ"
    output_png_file = LOGO_PATH / "banner.png"

    rich.print(f"Compiling {input_typ_file} to {output_png_file}")
    rich.print(f"Using font path: {FONTS_PATH}")

    try:
        typst.compile(
            input_typ_file,
            output=output_png_file,
            format="png",
            ppi=144.0,
            font_paths=[FONTS_PATH],
        )
        rich.print("Compilation successful.")
    except Exception as e:  # noqa: BLE001
        rich.print(f"Compilation failed: {e}")
        import traceback

        traceback.print_exc()
