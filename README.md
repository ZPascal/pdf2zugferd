# pdf2zugferd

Turn an invoice PDF exported from LibreOffice, OpenOffice or MS Office into a
**ZUGFeRD / Factur-X (EN 16931)** PDF: the original pages plus an embedded,
schema-validated `factur-x.xml`.

The invoice data is read straight from the PDF text layer, so no OCR is
needed for office-generated PDFs. Seller data and IBAN come from a config file.

> **Heads-up: template-based tool.** This is not a generic PDF-to-e-invoice
> converter. It only understands one fixed German invoice layout (see
> [Supported invoice layout](#supported-invoice-layout)) and issues invoices
> without VAT (Kleinunternehmer, § 19 UStG). PDFs with a different layout are
> rejected, not guessed. The output is provided as is, without warranty: validate
> it with your own validator before relying on it for legal purposes.

## Install

The tool is published on [PyPI](https://pypi.org/project/pdf2zugferd/) as
`pdf2zugferd` (Python >= 3.12). The package, the import name and the command
are all called `pdf2zugferd`.

```bash
uvx pdf2zugferd --help          # run without installing
pipx install pdf2zugferd        # or: pip install pdf2zugferd
```

## Usage

```bash
cp config.example.toml config.toml   # fill in your data
pdf2zugferd invoice.pdf -c config.toml        # -> invoice_zugferd.pdf
pdf2zugferd invoice.pdf -c config.toml -o out.pdf --xml-only --force
```

Without Python, download a single-file binary from the GitHub release
(Linux, Windows, macOS), or run from source with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
uv run pdf2zugferd invoice.pdf -c config.toml
```

## Supported invoice layout

The parser targets one fixed template (German labels `Rechnungsdatum`,
`Rechnungsnummer`, `Kundennummer`, a position table, `Betrag … €`,
`Zahlungsziel beträgt N Tage`). Totals are cross-checked and the tool aborts
instead of emitting a wrong e-invoice. Invoices are issued without VAT
(Kleinunternehmer, § 19 UStG, tax category `E`).

## Limitations

- The output is not converted to PDF/A-3 (fonts are not re-embedded). Most
  receiving software only needs the embedded XML; strict PDF/A validators may
  complain. Export the source as PDF/A-1b from LibreOffice if you need it.
- Scanned PDFs are rejected; run them through OCR (e.g. `ocrmypdf`) first.

## Development

```bash
uv run ruff format . && uv run ruff check .
uv run pytest                    # unit + e2e (CLI)
uv run bandit -r src && uv run pip-audit --skip-editable
```

## License

Apache-2.0, see [LICENSE](LICENSE).
