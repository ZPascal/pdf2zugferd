"""Plain data containers shared between extraction and XML generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Party:
    name: str
    street: str
    postcode: str
    city: str
    country: str = "DE"


@dataclass(frozen=True)
class Line:
    position: str
    name: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    total: Decimal
    unit_code: str = "DAY"


@dataclass(frozen=True)
class Invoice:
    number: str
    issue_date: date
    customer_number: str
    buyer: Party
    lines: list[Line] = field(default_factory=list)
    total: Decimal = Decimal(0)
    payment_days: int | None = None
