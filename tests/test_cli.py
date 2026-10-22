"""In-process tests so coverage sees the CLI and XML builder."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader

from pdf2zugferd import extract
from pdf2zugferd.cli import main


def test_main_writes_pdf_and_xml(
    invoice_pdf: Path, config_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    out = tmp_path / "o.pdf"
    assert (
        main([str(invoice_pdf), "-c", str(config_file), "-o", str(out), "--xml-only"])
        == 0
    )
    assert "factur-x.xml" in PdfReader(out).attachments
    assert out.with_suffix(".xml").read_bytes().startswith(b"<?xml")
    assert "wrote" in capsys.readouterr().out


def test_existing_output_needs_force(
    invoice_pdf: Path, config_file: Path, tmp_path: Path
) -> None:
    out = tmp_path / "o.pdf"
    out.write_bytes(b"old")
    args = [str(invoice_pdf), "-c", str(config_file), "-o", str(out)]
    assert main(args) == 2
    assert out.read_bytes() == b"old"
    assert main([*args, "--force"]) == 0


def test_config_error_is_reported(
    invoice_pdf: Path, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    assert main([str(invoice_pdf), "-c", str(tmp_path / "missing.toml")]) == 1
    assert "config file not found" in capsys.readouterr().err


def test_oversized_pdf_is_rejected(
    invoice_pdf: Path, config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(extract, "_MAX_BYTES", 10)
    assert main([str(invoice_pdf), "-c", str(config_file)]) == 1
