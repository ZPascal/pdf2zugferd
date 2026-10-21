"""Shared fixtures: a synthetic invoice that mimics the LibreOffice layout."""

from __future__ import annotations

from pathlib import Path

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

CONFIG = """\
[seller]
name = "Erika Musterfrau"
street = "Musterweg 1"
postcode = "12345"
city = "Musterstadt"
tax_number = "12/345/67890"
iban = "DE89 3704 0044 0532 0130 00"
bic = "COBADEFFXXX"
email = "erika@example.com"
"""


def make_invoice_pdf(path: Path, total: str = "800,00") -> Path:
    c = canvas.Canvas(str(path), pagesize=A4)
    rows = [
        (50, 800, "Erika Musterfrau | Musterweg 1 | 12345 Musterstadt"),
        (50, 760, "Herr Max Mustermann"),
        (50, 745, "Beispielstraße 7"),
        (50, 730, "54321 Beispielhausen"),
        (400, 700, "Rechnungsdatum:"),
        (400, 685, "15.04.2026"),
        (400, 665, "Rechnungsnummer:"),
        (400, 650, "1201"),
        (400, 630, "Kundennummer:"),
        (400, 615, "1200"),
        (400, 595, "Steuernummer:"),
        (400, 580, "12/345/67890"),
        (50, 540, "Rechnung"),
        (50, 510, "Pos. Bezeichnung Menge Einzel (€) Gesamt (€)"),
        (50, 490, "1 Lagercontainer in der Ausführung 1 Container 200 4,00 800,00"),
        (50, 475, "Seecontainer 20ft in Beispielhausen"),
        (50, 440, f"Betrag {total} €"),
        (50, 400, "Das Zahlungsziel beträgt 21 Tage."),
    ]
    for x, y, text in rows:
        c.drawString(x, y, text)
    c.save()
    return path


@pytest.fixture
def invoice_pdf(tmp_path: Path) -> Path:
    return make_invoice_pdf(tmp_path / "invoice.pdf")


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(CONFIG, encoding="utf-8")
    return path
