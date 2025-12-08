from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from app.core.settings import get_configs
from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def _ensure_test_commissions_defaults() -> None:
    """Force commission thresholds expected by tests, irrespective of local config edits.

    This preserves deterministic assertions in functional tests even if the
    runtime commissions.yml is modified (e.g., set to zeros to hide section in UI).
    """
    cfg = get_configs()
    cfg.commissions = {
        "thresholds": [
            {"max_price": 1_500_000, "amount": 40_000},
            {"max_price": 3_500_000, "amount": 65_000},
            {"amount": 85_000},
        ]
    }
