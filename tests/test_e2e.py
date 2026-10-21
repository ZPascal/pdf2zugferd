"""End-to-end: run the real CLI and inspect the produced ZUGFeRD PDF."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from lxml import etree
from pypdf import PdfReader

from .conftest import make_invoice_pdf

NS = {
    "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
    "ram": (
        "urn:un:unece:uncefact:data:standard:"
        "ReusableAggregateBusinessInformationEntity:100"
    ),
}


def _command() -> list[str]:
    binary = os.environ.get("PDF_TO_ZUGPFERD_BIN")
    if binary:
        return [binary]
    return [sys.executable, "-m", "pdf_to_zugpferd"]


def _embedded_xml(pdf: Path) -> etree._Element:
    attachments = PdfReader(pdf).attachments
    assert "factur-x.xml" in attachments
    return etree.fromstring(attachments["factur-x.xml"][0])


def _run(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*_command(), *map(str, args)], capture_output=True, text=True, check=False
    )


def test_convert_invoice(invoice_pdf: Path, config_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.pdf"
    result = _run(invoice_pdf, "-c", config_file, "-o", out)
    assert result.returncode == 0, result.stderr
    assert out.read_bytes().startswith(b"%PDF")

    xml = _embedded_xml(out)
    text = lambda path: xml.xpath(path, namespaces=NS)[0].text  # noqa: E731
    assert text("//rsm:ExchangedDocument/ram:ID") == "1201"
    assert text("//ram:SellerTradeParty/ram:Name") == "Erika Musterfrau"
    assert text("//ram:BuyerTradeParty/ram:Name") == "Max Mustermann"
    assert text("//ram:IBANID") == "DE89370400440532013000"
    assert text("//ram:GrandTotalAmount") == "800.00"
    due = xml.xpath("//ram:DueDateDateTime/*", namespaces=NS)[0].text
    assert due == "20260506"
    assert (
        text(
            "//ram:ApplicableHeaderTradeSettlement/ram:ApplicableTradeTax/ram:CategoryCode"
        )
        == "E"
    )


def test_original_is_untouched(
    invoice_pdf: Path, config_file: Path, tmp_path: Path
) -> None:
    before = invoice_pdf.read_bytes()
    assert (
        _run(invoice_pdf, "-c", config_file, "-o", tmp_path / "o.pdf").returncode == 0
    )
    assert invoice_pdf.read_bytes() == before


def test_default_output_name(invoice_pdf: Path, config_file: Path) -> None:
    assert _run(invoice_pdf, "-c", config_file).returncode == 0
    assert (invoice_pdf.parent / "invoice_zugferd.pdf").exists()


def test_refuses_to_overwrite_input(invoice_pdf: Path, config_file: Path) -> None:
    result = _run(invoice_pdf, "-c", config_file, "-o", invoice_pdf)
    assert result.returncode == 2


def test_bad_input_gives_clean_error(config_file: Path, tmp_path: Path) -> None:
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"nope")
    result = _run(bad, "-c", config_file)
    assert result.returncode == 1
    assert result.stderr.startswith("error:")
    assert "Traceback" not in result.stderr


def test_mismatching_total_fails(config_file: Path, tmp_path: Path) -> None:
    pdf = make_invoice_pdf(tmp_path / "bad.pdf", total="1,00")
    assert _run(pdf, "-c", config_file).returncode == 1
