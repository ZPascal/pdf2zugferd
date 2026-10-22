"""Seller configuration loaded from a TOML file kept outside the repository."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from .models import Party


class ConfigError(ValueError):
    """Raised when the configuration file is missing or incomplete."""


@dataclass(frozen=True)
class SellerConfig:
    party: Party
    tax_number: str
    iban: str
    bic: str | None
    email: str | None
    phone: str | None
    exemption_reason: str


_REQUIRED = ("name", "street", "postcode", "city", "tax_number", "iban")
_DEFAULT_REASON = (
    "Gemäß § 19 Abs. 1 UStG wird keine Umsatzsteuer als Kleinunternehmer ausgewiesen."
)


def _clean_iban(value: str) -> str:
    iban = "".join(value.split()).upper()
    if not (15 <= len(iban) <= 34) or not iban.isalnum():
        raise ConfigError("seller.iban is not a valid IBAN")
    digits = "".join(str(int(c, 36)) for c in iban[4:] + iban[:4])
    if int(digits) % 97 != 1:
        raise ConfigError("seller.iban has an invalid checksum")
    return iban


def load_config(path: Path) -> SellerConfig:
    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except FileNotFoundError as exc:
        raise ConfigError(f"config file not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"config file is not valid TOML: {exc}") from exc

    seller = data.get("seller")
    if not isinstance(seller, dict):
        raise ConfigError("config needs a [seller] table")
    missing = [k for k in _REQUIRED if not str(seller.get(k, "")).strip()]
    if missing:
        raise ConfigError(f"seller config is missing: {', '.join(missing)}")

    return SellerConfig(
        party=Party(
            name=seller["name"],
            street=seller["street"],
            postcode=str(seller["postcode"]),
            city=seller["city"],
            country=seller.get("country", "DE"),
        ),
        tax_number=seller["tax_number"],
        iban=_clean_iban(seller["iban"]),
        bic=seller.get("bic"),
        email=seller.get("email"),
        phone=seller.get("phone"),
        exemption_reason=seller.get("exemption_reason", _DEFAULT_REASON),
    )
