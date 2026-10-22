"""Build the ZUGFeRD / Factur-X (EN 16931) XML and embed it into the PDF."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from drafthorse.models.accounting import ApplicableTradeTax
from drafthorse.models.document import Document
from drafthorse.models.party import TaxRegistration
from drafthorse.models.payment import PaymentMeans, PaymentTerms
from drafthorse.models.tradelines import LineItem
from drafthorse.pdf import attach_xml

from .config import SellerConfig
from .models import Invoice, Party

_GUIDELINE = "urn:cen.eu:en16931:2017"
_ZERO = Decimal("0.00")


def _fill_party(target, party: Party) -> None:
    target.name = party.name
    target.address.line_one = party.street
    target.address.postcode = party.postcode
    target.address.city_name = party.city
    target.address.country_id = party.country


def build_xml(invoice: Invoice, seller: SellerConfig) -> bytes:
    doc = Document()
    doc.context.guideline_parameter.id = _GUIDELINE
    doc.header.id = invoice.number
    doc.header.type_code = "380"
    doc.header.issue_date_time = invoice.issue_date

    for item in invoice.lines:
        line = LineItem()
        line.document.line_id = item.position
        line.product.name = item.name
        if item.description:
            line.product.description = item.description
        line.agreement.net.amount = item.unit_price
        line.delivery.billed_quantity = (item.quantity, item.unit_code)
        line.settlement.trade_tax.type_code = "VAT"
        line.settlement.trade_tax.category_code = "E"
        line.settlement.trade_tax.rate_applicable_percent = _ZERO
        line.settlement.monetary_summation.total_amount = item.total
        doc.trade.items.add(line)

    _fill_party(doc.trade.agreement.seller, seller.party)
    doc.trade.agreement.seller.tax_registrations.add(
        TaxRegistration(id=("FC", seller.tax_number))
    )
    if seller.email:
        doc.trade.agreement.seller.electronic_address.uri_ID = ("EM", seller.email)
    _fill_party(doc.trade.agreement.buyer, invoice.buyer)
    doc.trade.agreement.buyer.id = invoice.customer_number

    settlement = doc.trade.settlement
    settlement.currency_code = "EUR"
    means = PaymentMeans()
    means.type_code = "58"  # SEPA credit transfer
    means.payee_account.iban = seller.iban
    if seller.bic:
        means.payee_institution.bic = seller.bic
    settlement.payment_means.add(means)

    tax = ApplicableTradeTax()
    tax.calculated_amount = _ZERO
    tax.basis_amount = invoice.total
    tax.type_code = "VAT"
    tax.category_code = "E"
    tax.exemption_reason = seller.exemption_reason
    tax.rate_applicable_percent = _ZERO
    settlement.trade_tax.add(tax)

    if invoice.payment_days is not None:
        terms = PaymentTerms()
        terms.due = invoice.issue_date + timedelta(days=invoice.payment_days)
        settlement.terms.add(terms)

    summation = settlement.monetary_summation
    summation.line_total = invoice.total
    summation.charge_total = _ZERO
    summation.allowance_total = _ZERO
    summation.tax_basis_total = invoice.total
    summation.tax_total = (_ZERO, "EUR")
    summation.grand_total = invoice.total
    summation.due_amount = invoice.total

    return doc.serialize(schema="FACTUR-X_EN16931")


def embed(pdf_path: Path, xml: bytes, output: Path) -> None:
    result = attach_xml(pdf_path.read_bytes(), xml, level="EN 16931")
    output.write_bytes(result)
