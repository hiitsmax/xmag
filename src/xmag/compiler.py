"""Compile generated LaTeX into PDF using Tectonic."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class TectonicCompileError(RuntimeError):
    """Raised when Tectonic fails to compile a .tex file."""


def compile_tex_with_tectonic(tex_path: Path, output_path: Path) -> None:
    """Compile tex_path with tectonic and move PDF artifact to output_path."""

    if shutil.which("tectonic") is None:
        raise TectonicCompileError(
            "Tectonic not found. Install it and ensure `tectonic` is on PATH."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = ["tectonic", "--outdir", str(output_path.parent), str(tex_path)]
    process = subprocess.run(command, capture_output=True, text=True, check=False)
    if process.returncode != 0:
        raise TectonicCompileError(process.stderr.strip() or "Unknown Tectonic compile failure")

    generated_pdf = output_path.parent / f"{tex_path.stem}.pdf"
    if not generated_pdf.exists():
        raise TectonicCompileError(f"Expected output PDF not found: {generated_pdf}")

    if generated_pdf.resolve() != output_path.resolve():
        if output_path.exists():
            output_path.unlink()
        generated_pdf.rename(output_path)
