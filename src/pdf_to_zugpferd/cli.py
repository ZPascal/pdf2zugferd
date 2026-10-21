"""Command line entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import ConfigError, load_config
from .extract import ExtractionError, extract_invoice
from .zugferd import build_xml, embed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf-to-zugpferd",
        description="Convert an invoice PDF into a ZUGFeRD (EN 16931) PDF.",
    )
    parser.add_argument("pdf", type=Path, help="input invoice PDF")
    parser.add_argument(
        "-c", "--config", type=Path, required=True, help="seller TOML config"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output PDF (default: <input>_zugferd.pdf next to the input)",
    )
    parser.add_argument(
        "--xml-only", action="store_true", help="also write the XML next to the output"
    )
    parser.add_argument(
        "--force", action="store_true", help="overwrite existing output files"
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pdf: Path = args.pdf
    output: Path = args.output or pdf.with_name(f"{pdf.stem}_zugferd.pdf")
    if output.resolve() == pdf.resolve():
        print("error: output must differ from input", file=sys.stderr)
        return 2
    xml_path = output.with_suffix(".xml")
    targets = [output, xml_path] if args.xml_only else [output]
    existing = [t for t in targets if t.exists()]
    if existing and not args.force:
        print(f"error: {existing[0]} exists (use --force)", file=sys.stderr)
        return 2
    try:
        seller = load_config(args.config)
        invoice = extract_invoice(pdf)
        xml = build_xml(invoice, seller)
        embed(pdf, xml, output)
        if args.xml_only:
            xml_path.write_bytes(xml)
    except (ConfigError, ExtractionError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
