from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from pdf_to_zugpferd.extract import (
    ExtractionError,
    extract_invoice,
    parse_invoice,
    read_text,
)

from .conftest import make_invoice_pdf


def test_extracts_all_fields(invoice_pdf: Path) -> None:
    inv = extract_invoice(invoice_pdf)
    assert inv.number == "1201"
    assert inv.issue_date == date(2026, 4, 15)
    assert inv.customer_number == "1200"
    assert inv.buyer.name == "Max Mustermann"
    assert inv.buyer.postcode == "54321"
    assert inv.buyer.city == "Beispielhausen"
    assert inv.total == Decimal("800.00")
    assert inv.payment_days == 21
    (line,) = inv.lines
    assert line.quantity == Decimal(200)
    assert line.unit_price == Decimal("4.00")
    assert "Seecontainer" in line.description


def test_total_mismatch_is_rejected(tmp_path: Path) -> None:
    pdf = make_invoice_pdf(tmp_path / "bad.pdf", total="900,00")
    with pytest.raises(ExtractionError, match="add up"):
        extract_invoice(pdf)


def test_pdf_without_text_is_rejected(tmp_path: Path) -> None:
    from reportlab.pdfgen import canvas

    path = tmp_path / "empty.pdf"
    c = canvas.Canvas(str(path))
    c.showPage()
    c.save()
    with pytest.raises(ExtractionError, match="no text layer"):
        read_text(path)


def test_garbage_file_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "x.pdf"
    path.write_bytes(b"not a pdf")
    with pytest.raises(ExtractionError, match="cannot read PDF"):
        read_text(path)


def test_missing_field_is_reported() -> None:
    with pytest.raises(ExtractionError, match="Rechnungsdatum"):
        parse_invoice("Rechnung\nnothing here")
