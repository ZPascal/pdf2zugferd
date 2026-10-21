# Security policy

Please report vulnerabilities privately via GitHub's "Report a vulnerability"
button on the Security tab instead of opening a public issue.

## Hardening in place

- Untrusted PDFs are only read as text; nothing in them is executed.
- Input is capped at 20 MiB and 20 pages to limit resource exhaustion.
- The tool never overwrites its input and refuses to overwrite existing
  output without `--force`.
- Seller data (including the IBAN) lives in a user-supplied TOML file that is
  git-ignored; IBANs are checksum-validated.
- XML is produced by `drafthorse` (escaped, XSD-validated), never by string
  concatenation.
- CI runs `bandit` and `pip-audit`; Dependabot keeps dependencies and
  GitHub Actions current. Workflows use read-only token permissions.
