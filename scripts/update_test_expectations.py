#!/usr/bin/env python3
"""
Helper script to update expected values in cases.yml based on actual API responses.
Runs each test case through the API and captures the actual results.
IMPORTANT: Uses test configuration to ensure consistency with pytest.
"""

from datetime import UTC, datetime
import os
from pathlib import Path
import sys

from fastapi.testclient import TestClient
import yaml


# Force static rates (disable live CBR) BEFORE importing app
os.environ["ENABLE_LIVE_CBR"] = "false"

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.settings import CONFIG_DIR, ConfigRegistry, get_configs
from app.main import app


BASE_DIR = Path(__file__).resolve().parents[1]  # Go up one level from scripts/
CASES_FILE = BASE_DIR / "tests" / "test_data" / "cases.yml"


def main():
    """Update expected values in cases.yml using test configuration"""

    # Load test commissions config (same as tests use in conftest.py)
    test_commissions_path = BASE_DIR / "tests" / "test_data" / "config" / "commissions_company_only.yml"
    if test_commissions_path.exists():
        print("Loading test configuration...")
        base_fees = yaml.safe_load((CONFIG_DIR / "fees.yml").read_text(encoding="utf-8")) or {}
        base_rates = yaml.safe_load((CONFIG_DIR / "rates.yml").read_text(encoding="utf-8")) or {}
        base_duties = yaml.safe_load((CONFIG_DIR / "duties.yml").read_text(encoding="utf-8")) or {}
        test_commissions = yaml.safe_load(test_commissions_path.read_text(encoding="utf-8")) or {}

        # Replace config (same as conftest.py does)
        cfg = get_configs()
        cfg.__dict__.update(
            ConfigRegistry(
                fees=base_fees,
                commissions=test_commissions,
                rates=base_rates,
                duties=base_duties,
                hash=cfg.hash,
                loaded_at=cfg.loaded_at,  # Preserve original loaded_at timestamp
            ).__dict__
        )
        print(f"✓ Using test commissions and static rates:")
        print(f"  EUR_RUB: {base_rates['currencies']['EUR_RUB']}")
        print(f"  USD_RUB: {base_rates['currencies']['USD_RUB']}")
        print(f"  JPY_RUB: {base_rates['currencies']['JPY_RUB']}")
        print(f"  CNY_RUB: {base_rates['currencies']['CNY_RUB']}")
        print(f"  AED_RUB: {base_rates['currencies']['AED_RUB']}")
        print()

    # Load cases
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    client = TestClient(app)
    current_year = datetime.now(UTC).year

    cases = data["cases"]
    updated_count = 0

    for case in cases:
        name = case["name"]
        print(f"Processing case: {name}")

        # Prepare request
        req_payload = dict(case["request"])
        if "year" not in req_payload:
            age_offset = int(case.get("age_offset", 1))
            req_payload["year"] = current_year - age_offset

        # Make API call
        try:
            r = client.post("/api/calculate", json=req_payload)
            if r.status_code != 200:
                print(f"  ERROR: {r.status_code} - {r.text}")
                continue

            result = r.json()
            meta = result["meta"]
            breakdown = result["breakdown"]

            # Update expected values
            case["expected"]["age_category"] = meta["age_category"]
            case["expected"]["purchase_price_rub"] = int(round(breakdown["purchase_price_rub"]))
            case["expected"]["duties_rub"] = int(round(breakdown["duties_rub"]))
            case["expected"]["utilization_fee_rub"] = int(round(breakdown["utilization_fee_rub"]))
            case["expected"]["customs_services_rub"] = int(round(breakdown["customs_services_rub"]))
            case["expected"]["era_glonass_rub"] = int(round(breakdown["era_glonass_rub"]))
            case["expected"]["freight_rub"] = int(round(breakdown["freight_rub"]))
            case["expected"]["country_expenses_rub"] = int(round(breakdown["country_expenses_rub"]))
            case["expected"]["company_commission_rub"] = int(round(breakdown["company_commission_rub"]))
            case["expected"]["total_rub"] = int(round(breakdown["total_rub"]))

            updated_count += 1
            print(f"  ✓ Updated")

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    # Save updated cases
    with open(CASES_FILE, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"\n✅ Updated {updated_count}/{len(cases)} cases")
    print(f"📝 Saved to {CASES_FILE}")


if __name__ == "__main__":
    main()

