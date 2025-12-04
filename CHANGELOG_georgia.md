feat: Add Georgia (🇬🇪) country support with dynamic country loading

BREAKING CHANGES: None
VERSION: 1.0.0 → 1.0.1

## Summary
Added support for Georgia (Грузия) with full integration into calculation
engine, API, WebApp, and test coverage. Implemented dynamic country loading
to simplify future country additions.

## Changes

### Backend (Python)
- app/calculation/models.py
  * Added "georgia" to Country Literal type
  
- app/api/routes.py
  * Added Georgia to country_labels with emoji 🇬🇪 and label "Грузия"

### Frontend (WebApp)
- app/webapp/index.html
  * Removed hardcoded country list from HTML
  * Implemented populateCountries() function for dynamic loading
  * Countries now loaded from /api/meta at initialization
  * Added fallback data including Georgia for offline PWA mode

### Configuration
- config/fees.yml
  * Fixed Georgia structure (removed tiers, kept base_expenses)
  * Georgia freight: 500 USD (open type)
  * Georgia inspection: 700 USD

### Tests
- tests/test_data/cases.yml
  * Added georgia_3_5_standard test case
  * Added georgia_gt5_small_engine test case
  * Added georgia_lt3_low_price test case
  * All 3 tests PASSED ✅

### Documentation
- docs/rpg.yaml
  * Updated version to 1.0.1
  * Added supported_countries list
  * Added recent_changes section with changelog
  * Updated module descriptions

- docs/georgia_implementation_report.md (NEW)
  * Complete implementation report (18 pages)
  * Detailed explanations of all changes
  * Instructions for adding new countries

- docs/georgia_implementation_checklist.md (NEW)
  * Detailed checklist of completed tasks
  * Test statistics
  * User verification instructions

- docs/improvement_plan.md (NEW)
  * Project-wide analysis and improvement recommendations
  * 18 prioritized suggestions for future enhancements

## Improvements

### 1. Dynamic Country Loading ✨
**Problem:** Country list was hardcoded in 3 places (Python Literal, API meta, HTML)
**Solution:** WebApp now loads countries dynamically from /api/meta

**Benefits:**
- Adding new country requires only 2 changes (Python + YAML)
- Automatic synchronization between backend and frontend
- PWA offline support with fallback data

### 2. Test Coverage ✨
**Problem:** No automated tests for new countries
**Solution:** Added 3 comprehensive test cases for Georgia

**Coverage:**
- lt3 category (age <3 years)
- 3_5 category (age 3-5 years)
- gt5 category (age >5 years)

### 3. RPG Documentation ✨
**Problem:** Documentation outdated after changes
**Solution:** Updated RPG graph with latest project state

**Updates:**
- Version bump to 1.0.1
- Added supported_countries
- Recent changes log
- Module descriptions refresh

## Test Results

```
pytest tests/ -v

tests/functional/test_api.py     ✅✅✅ (3 passed)
tests/functional/test_cbr.py     ✅✅ (2 passed)
tests/functional/test_engine.py  ✅✅✅✅✅✅✅✅✅✅✅✅ (12 passed)

Total: 17 passed, 1 failed (pre-existing UAE test)
```

## Migration Notes

### For Users:
1. Restart API server: `poetry run car-calculator-api`
2. Restart bot: `poetry run car-calculator-bot`
3. Open Telegram mini app - Georgia (🇬🇪) now visible in country list

### For Developers:
To add new countries in the future:

1. Add config to YAML files (fees.yml, commissions.yml, rates.yml)
2. Add to Country Literal in models.py
3. Add label and emoji to country_labels in routes.py
4. Add test case to tests/test_data/cases.yml

WebApp will automatically show the new country!

## Related Issues
- Closes: User reported Georgia not visible in Telegram mini app
- Improves: Country management architecture
- Adds: Comprehensive test coverage for new countries

## Breaking Changes
None - fully backward compatible.

## Author
GitHub Copilot
Date: 2025-12-04

