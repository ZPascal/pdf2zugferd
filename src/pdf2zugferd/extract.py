"""Extract invoice data from a text-based PDF produced by an office suite."""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pdfplumber

from .models import Invoice, Line, Party


class ExtractionError(ValueError):
    """Raised when the PDF does not contain the expected invoice layout."""


_MAX_PAGES = 20
_MAX_BYTES = 20 * 1024 * 1024  # refuse absurdly large inputs (DoS guard)
_AMOUNT = r"\d{1,3}(?:\.\d{3})*,\d{2}"
_LINE_RE = re.compile(
    rf"^(?P<pos>\d+)\s+(?P<name>.+?)\s+(?P<menge>\d+\s+\S+)\s+"
    rf"(?P<qty>\d+(?:,\d+)?)\s+(?P<price>{_AMOUNT})\s+(?P<total>{_AMOUNT})$"
)
_SIMPLE_LINE_RE = re.compile(
    rf"^(?P<pos>\d+)\s+(?P<name>.+?)\s+(?P<qty>\d+(?:,\d+)?)\s+(?P<unit>[^\d\s]\S*)\s+"
    rf"(?P<price>{_AMOUNT})\s+(?P<total>{_AMOUNT})$"
)
# UN/ECE Rec. 20 codes for the units seen on German invoices.
_UNIT_CODES = {
    "monat": "MON",
    "monate": "MON",
    "tag": "DAY",
    "tage": "DAY",
    "stunde": "HUR",
    "stunden": "HUR",
    "stück": "C62",
    "stk": "C62",
}
_STOP_RE = re.compile(r"^(Betrag\b|Summe\b|Gesamt)")
_POSTCODE_RE = re.compile(r"^(?P<zip>\d{5})\s+(?P<city>.+)$")


def _decimal(text: str) -> Decimal:
    try:
        return Decimal(text.replace(".", "").replace(",", "."))
    except InvalidOperation as exc:
        raise ExtractionError(f"cannot parse amount: {text!r}") from exc


def _field(text: str, label: str) -> str:
    match = re.search(rf"{label}:\s*\n?\s*(\S[^\n]*)", text)
    if not match:
        raise ExtractionError(f"field not found in PDF: {label}")
    return match.group(1).strip()


def read_text(path: Path) -> str:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ExtractionError(f"cannot read PDF {path}: {exc}") from exc
    if size > _MAX_BYTES:
        raise ExtractionError(f"PDF is larger than {_MAX_BYTES // 2**20} MiB")
    try:
        with pdfplumber.open(path) as pdf:
            pages = pdf.pages[:_MAX_PAGES]
            text = "\n".join(page.extract_text() or "" for page in pages)
    except Exception as exc:  # pdfminer raises many unrelated types
        raise ExtractionError(f"cannot read PDF {path}: {exc}") from exc
    if not text.strip():
        raise ExtractionError(
            "PDF has no text layer (scanned?). Run it through OCR first."
        )
    return text


def _parse_buyer(lines: list[str]) -> Party:
    # Layout: sender line, then salutation+name, street, "PLZ City".
    for idx, line in enumerate(lines):
        match = _POSTCODE_RE.match(line)
        if match and idx >= 3:
            name = re.sub(r"^(Herr|Frau|Firma)\s+", "", lines[idx - 2])
            return Party(
                name=name,
                street=lines[idx - 1],
                postcode=match["zip"],
                city=match["city"],
            )
    raise ExtractionError("buyer address block not found")


def _unit_code(match: re.Match[str]) -> str:
    if "unit" not in match.groupdict() or match["unit"] is None:
        return "DAY"
    return _UNIT_CODES.get(match["unit"].lower(), "C62")


def _parse_lines(lines: list[str]) -> list[Line]:
    matches: list[tuple[re.Match[str], list[str]]] = []
    for line in lines:
        match = _LINE_RE.match(line) or _SIMPLE_LINE_RE.match(line)
        if match:
            matches.append((match, []))
        elif _STOP_RE.match(line):
            break
        elif matches:
            matches[-1][1].append(line)
    return [
        Line(
            position=m["pos"],
            name=m["name"],
            description=" ".join(extra),
            quantity=_decimal(m["qty"]),
            unit_price=_decimal(m["price"]),
            total=_decimal(m["total"]),
            unit_code=_unit_code(m),
        )
        for m, extra in matches
    ]


def parse_invoice(text: str) -> Invoice:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    try:
        issue = datetime.strptime(_field(text, "Rechnungsdatum"), "%d.%m.%Y").date()
    except ValueError as exc:
        raise ExtractionError(f"invalid invoice date: {exc}") from exc

    items = _parse_lines(lines)
    if not items:
        raise ExtractionError("no invoice line items found")

    total_match = re.search(rf"^Betrag\s+({_AMOUNT})\s*€", text, re.MULTILINE)
    if not total_match:
        raise ExtractionError("invoice total ('Betrag') not found")
    total = _decimal(total_match.group(1))
    if sum((i.total for i in items), Decimal(0)) != total:
        raise ExtractionError("line totals do not add up to the invoice total")
    for item in items:
        if item.quantity * item.unit_price != item.total:
            raise ExtractionError(f"line {item.position}: quantity x price != total")

    days = re.search(r"Zahlungsziel beträgt (\d+) Tage", text)
    return Invoice(
        number=_field(text, "Rechnungsnummer"),
        issue_date=issue,
        customer_number=_field(text, "Kundennummer"),
        buyer=_parse_buyer(lines),
        lines=items,
        total=total,
        payment_days=int(days.group(1)) if days else None,
    )


def extract_invoice(path: Path) -> Invoice:
    return parse_invoice(read_text(path))
