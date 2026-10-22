from pathlib import Path

import pytest

from pdf2zugpferd.config import ConfigError, load_config


def test_loads_and_normalises_iban(config_file: Path) -> None:
    cfg = load_config(config_file)
    assert cfg.iban == "DE89370400440532013000"
    assert cfg.party.city == "Musterstadt"
    assert "§ 19" in cfg.exemption_reason


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nope.toml")


def test_invalid_toml(tmp_path: Path) -> None:
    path = tmp_path / "c.toml"
    path.write_text("[seller", encoding="utf-8")
    with pytest.raises(ConfigError, match="not valid TOML"):
        load_config(path)


def test_missing_keys(tmp_path: Path) -> None:
    path = tmp_path / "c.toml"
    path.write_text('[seller]\nname = "x"\n', encoding="utf-8")
    with pytest.raises(ConfigError, match="missing"):
        load_config(path)


def test_bad_iban_checksum(config_file: Path, tmp_path: Path) -> None:
    path = tmp_path / "c2.toml"
    path.write_text(config_file.read_text().replace("3704", "3705"), encoding="utf-8")
    with pytest.raises(ConfigError, match="checksum"):
        load_config(path)
