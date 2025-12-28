from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest
import yaml

from app.core.settings import CONFIG_DIR, ConfigRegistry, get_configs
from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def _ensure_test_commissions_defaults() -> None:
    """Force test commissions config compatible with SPEC.

    Instead of legacy "thresholds" structure, load a dedicated test YAML
    so that functional tests use a deterministic commissions config that
    matches the v2 schema (default_commission_usd/by_country).
    """
    # Build path to test commissions YAML (company commission only)
    test_commissions_path = (
        Path(__file__).resolve().parent / "test_data" / "config" / "commissions_company_only.yml"
    )

    if not test_commissions_path.exists():  # pragma: no cover - defensive
        # Fallback to runtime config if test file is missing
        return

    # Load all base configs from the standard CONFIG_DIR
    base_fees = yaml.safe_load((CONFIG_DIR / "fees.yml").read_text(encoding="utf-8")) or {}
    base_rates = yaml.safe_load((CONFIG_DIR / "rates.yml").read_text(encoding="utf-8")) or {}
    base_duties = yaml.safe_load((CONFIG_DIR / "duties.yml").read_text(encoding="utf-8")) or {}

    # Load test commissions from YAML
    test_commissions = yaml.safe_load(test_commissions_path.read_text(encoding="utf-8")) or {}

    # Replace the cached ConfigRegistry instance with a test instance
    # so that all code using get_configs() sees the test commissions.
    cfg = get_configs()
    cfg.__dict__.update(
        ConfigRegistry(
            fees=base_fees,
            commissions=test_commissions,
            rates=base_rates,
            duties=base_duties,
            hash=cfg.hash,
            loaded_at=cfg.loaded_at,
        ).__dict__
    )
