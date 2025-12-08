# Sprint 7 Commit Guide

## Recommended Git Commands

```bash
# Add all modified files
git add app/bot/handlers/start.py
git add tests/manual/test_bot_handlers_sprint7.py
git add docs/SPRINT_7_SUMMARY.md
git add docs/rpg.yaml

# Check what's staged
git status

# Commit with detailed message
git commit -m "feat(bot): add engine_power_hp support in Telegram Bot handlers

SPRINT 7 COMPLETED:

Added:
- _format_result() helper for HTML formatting with power display
- engine_power_hp=110 in cmd_calc example
- engine_power_hp parsing and validation in on_webapp_data
- Power display in kW alongside HP
- Utilization coefficient display in breakdown
- Comprehensive error handling (ValidationError + generic)
- Manual test suite (4 tests, all passing)

Updated:
- cmd_calc: uses new field, integrates _format_result
- on_webapp_data: parses engine_power_hp, validates required field
- Imports: added Decimal, ValidationError, CalculationResult
- Documentation: rpg.yaml with Sprint 7 completion

Tests:
- test_bot_handlers_sprint7.py: 4/4 tests passing
- Validates calculations, formatting, parsing, validation
- Bot module imports successfully
- Syntax check passed

Breaking Changes: None (backward compatible)

See: docs/SPRINT_7_SUMMARY.md"
```

## Alternative: Short Commit Message

```bash
git commit -m "feat(bot): add engine_power_hp support in handlers

- Add _format_result() for consistent HTML formatting
- Update cmd_calc with engine_power_hp=110
- Parse and validate engine_power_hp in on_webapp_data
- Display power in kW and utilization coefficient
- Add comprehensive error handling
- Create manual test suite (4/4 passing)

Sprint 7 complete. See docs/SPRINT_7_SUMMARY.md"
```

## Verify Before Push

```bash
# Run manual tests one more time
python tests/manual/test_bot_handlers_sprint7.py

# Check imports work
python -c "from app.bot.handlers.start import _format_result, cmd_calc, on_webapp_data; print('✅ OK')"

# Verify syntax
python -m py_compile app/bot/handlers/start.py

# Check for uncommitted changes
git status

# Review diff
git diff --staged
```

## Push to Remote

```bash
# Push to your branch
git push origin sprint-7-bot-handlers

# Or if on main:
git push origin main
```

## Create PR (if using GitHub/GitLab)

**Title:** `feat(bot): Add engine_power_hp support in Telegram Bot handlers (Sprint 7)`

**Description:**
```markdown
## Sprint 7: Telegram Bot Handler Updates

### Summary
Updates Telegram Bot handlers to support the new `engine_power_hp` field introduced in the 2025 utilization fee system.

### Changes
- ✅ Created `_format_result()` helper for consistent HTML formatting
- ✅ Updated `cmd_calc` command with `engine_power_hp=110` example
- ✅ Updated `on_webapp_data` to parse and validate `engine_power_hp`
- ✅ Added power display in both HP and kW
- ✅ Added utilization coefficient display in breakdown
- ✅ Comprehensive error handling (ValidationError, generic exceptions)
- ✅ Created manual test suite (4 tests, all passing)

### Testing
- [x] Manual tests: 4/4 passing
- [x] Syntax validation passed
- [x] Import checks passed
- [x] Bot module loads successfully

### Documentation
- [x] Updated `docs/rpg.yaml` with Sprint 7 completion
- [x] Created `docs/SPRINT_7_SUMMARY.md` with full details
- [x] Updated docstrings and inline comments

### Example Output
```
💰 Расчёт стоимости растаможки

🇯🇵 Страна: JAPAN
📅 Год: 2021 (3_5)
⚙️ Объём: 1496 см³
🔋 Мощность: 110 л.с. (80.91 кВт)    ← NEW!
💵 Цена: 2,500,000 JPY

📊 Детализация:
• Таможенная пошлина: 225,589 ₽
• Утилизационный сбор: 5,200 ₽
  (базовая ставка 20,000 ₽ × коэфф. 0.26)    ← NEW!
...
```

### Breaking Changes
None - fully backward compatible.

### Related
- Depends on: Sprint 1-6 (backend, API, WebApp)
- Enables: Sprint 8 (comprehensive testing)

### Checklist
- [x] Code follows project style
- [x] Tests added and passing
- [x] Documentation updated
- [x] No breaking changes
- [x] Ready for production
```

## Tags (Optional)

```bash
# Tag this sprint completion
git tag -a v2.0.0-sprint7 -m "Sprint 7: Bot handlers with engine_power_hp support"
git push origin v2.0.0-sprint7
```

## Notes

- This commit completes Sprint 7 of the refactoring plan
- All tests pass, no breaking changes
- Bot is ready for production deployment
- See `docs/SPRINT_7_SUMMARY.md` for full details

