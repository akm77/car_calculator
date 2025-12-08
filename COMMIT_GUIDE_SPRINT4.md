# Git Commit Guide for Sprint 4

## Commit Message

```
feat(config): update duties lt3 brackets to 2025 spec + fix commission UAE

SPRINT 4 COMPLETED:
- Updated duties.yml: 6 lt3 brackets (325k-6500k RUB → 3250-65000 EUR)
- Fixed commissions.yml: UAE exception (commission_usd: 0)
- Fixed engine.py: _commission() supports new dict structure
- Created test_sprint4_duties.py: 7 tests (all passing ✅)
- Updated documentation: rpg.yaml, REFACTORING_PROGRESS.md
- Created backup: duties_v1_backup_20251208.yml

BREAKING CHANGES:
- Lt3 duty thresholds changed (affects calculations for cars ≤3 years)
- Old thresholds: 8500, 16700, 42300, 84500, 169000 EUR
- New thresholds: 3250, 6500, 16250, 32500, 65000 EUR

TESTS:
✅ All 7 manual tests pass
✅ Config loading validated
✅ Commission logic confirmed (1000 USD + UAE=0)

Progress: 40% → 50% (5 of 10 sprints complete)

Refs: docs/SPRINT_4_SUMMARY.md, docs/sprint_prompts/SPRINT_4_DUTIES_COMMISSIONS.md
```

## Files to Add

```bash
git add app/calculation/engine.py
git add config/commissions.yml
git add config/duties.yml
git add config/duties_v1_backup_20251208.yml
git add docs/REFACTORING_PROGRESS.md
git add docs/SPRINT_4_SUMMARY.md
git add docs/rpg.yaml
git add test_sprint4_duties.py
```

## Alternative: Staged Commit

If you want to commit in stages:

### Commit 1: Config Changes
```bash
git add config/duties.yml config/commissions.yml config/duties_v1_backup_20251208.yml
git commit -m "feat(config): update duties lt3 brackets to 2025 spec (325k-6500k RUB)"
```

### Commit 2: Code Fix
```bash
git add app/calculation/engine.py
git commit -m "fix(engine): update _commission() to support commission_usd in by_country"
```

### Commit 3: Tests
```bash
git add test_sprint4_duties.py
git commit -m "test: add Sprint 4 duties and commissions tests (7 tests, all passing)"
```

### Commit 4: Documentation
```bash
git add docs/REFACTORING_PROGRESS.md docs/SPRINT_4_SUMMARY.md docs/rpg.yaml
git commit -m "docs: update Sprint 4 completion (progress 40%→50%)"
```

## Recommended: Single Atomic Commit

For sprint completion, a single atomic commit is cleaner:

```bash
# Add all Sprint 4 changes
git add app/calculation/engine.py \
        config/commissions.yml \
        config/duties.yml \
        config/duties_v1_backup_20251208.yml \
        docs/REFACTORING_PROGRESS.md \
        docs/SPRINT_4_SUMMARY.md \
        docs/rpg.yaml \
        test_sprint4_duties.py

# Commit with detailed message
git commit -F- <<'EOF'
feat(config): update duties lt3 brackets to 2025 spec + fix commission UAE

SPRINT 4 COMPLETED:
- Updated duties.yml: 6 lt3 brackets (325k-6500k RUB → 3250-65000 EUR)
- Fixed commissions.yml: UAE exception (commission_usd: 0)
- Fixed engine.py: _commission() supports new dict structure
- Created test_sprint4_duties.py: 7 tests (all passing ✅)
- Updated documentation: rpg.yaml, REFACTORING_PROGRESS.md
- Created backup: duties_v1_backup_20251208.yml

BREAKING CHANGES:
- Lt3 duty thresholds changed (affects calculations for cars ≤3 years)
- Old thresholds: 8500, 16700, 42300, 84500, 169000 EUR
- New thresholds: 3250, 6500, 16250, 32500, 65000 EUR

TESTS:
✅ All 7 manual tests pass
✅ Config loading validated
✅ Commission logic confirmed (1000 USD + UAE=0)

Progress: 40% → 50% (5 of 10 sprints complete)

Refs: docs/SPRINT_4_SUMMARY.md
EOF
```

## Verification After Commit

```bash
# View commit
git log -1 --stat

# Verify tests still pass
python test_sprint4_duties.py

# Verify config loads
python -c "from app.core.settings import get_configs; get_configs(); print('✅ OK')"
```

## Push to Remote

```bash
git push origin feature/spec-2025-utilization-upgrade
```

---

**Note**: Make sure you're on the correct branch before committing!
```bash
git branch --show-current
# Should show: feature/spec-2025-utilization-upgrade
```

