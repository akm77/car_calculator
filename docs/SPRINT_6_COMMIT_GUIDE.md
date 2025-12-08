# Git Commit Guide for Sprint 6

## Recommended Commit Message

```
feat(webapp): add engine_power_hp field with validation and result display

SPRINT 6 COMPLETE: Integrated engine power field into WebApp interface

Changes:
- Added HTML form field "Мощность двигателя (л.с.)" after engineCc
- Updated constants.js: ENGINE_POWER_HP_MIN/MAX (1-1500), CONVERSION_FACTORS (HP↔kW)
- Updated validator.js: validateField('engine_power_hp') with min/max/required checks
- Updated messages.js: enginePowerHpRequired, ENGINE_POWER_HP label, breakdown labels
- Updated calculateCost(): passes engine_power_hp to API
- Updated displayResult(): shows power in kW and utilization coefficient
- Added real-time validation on blur
- Created test_engine_power_field.html (16 tests, all passing)
- Updated rpg.yaml with Sprint 6 completion

Integration verified:
✅ API accepts engine_power_hp parameter
✅ Response includes meta.engine_power_kw and utilization_coefficient
✅ Frontend displays power conversion and coefficient calculation
✅ No linting/console errors

Files modified: 5
Files created: 3 (test + docs)
Test coverage: 16 unit tests + 1 integration test
Time: 2.5 hours (under estimate)

Closes: Sprint 6 Frontend WebApp
Refs: docs/sprint_prompts/SPRINT_6_FRONTEND_WEBAPP.md
Next: Sprint 7 Telegram Bot Integration
```

## Git Commands

```bash
# Stage all changes
git add app/webapp/index.html \
        app/webapp/js/config/constants.js \
        app/webapp/js/modules/validator.js \
        app/webapp/js/config/messages.js \
        docs/rpg.yaml \
        tests/manual/test_engine_power_field.html \
        docs/SPRINT_6_SUMMARY.md \
        SPRINT_6_CHECKLIST.md

# Commit with message
git commit -F - <<EOF
feat(webapp): add engine_power_hp field with validation and result display

SPRINT 6 COMPLETE: Integrated engine power field into WebApp interface

Changes:
- Added HTML form field "Мощность двигателя (л.с.)" after engineCc
- Updated constants.js: ENGINE_POWER_HP_MIN/MAX (1-1500), CONVERSION_FACTORS
- Updated validator.js: validateField('engine_power_hp') with validation
- Updated messages.js: error messages, labels, breakdown labels
- Updated calculateCost(): passes engine_power_hp to API
- Updated displayResult(): shows power in kW and utilization coefficient
- Added real-time validation on blur
- Created comprehensive test suite (16 tests passing)
- Updated rpg.yaml documentation

Integration verified:
✅ API accepts engine_power_hp and returns converted values
✅ Frontend displays power conversion (110 л.с. → 80.91 кВт)
✅ Utilization coefficient displayed with calculation explanation
✅ All validation tests passing
✅ No errors in browser console

Files: 5 modified, 3 created
Tests: 16 unit + 1 integration (all passing)
Time: 2.5h (under estimate)

Refs: docs/sprint_prompts/SPRINT_6_FRONTEND_WEBAPP.md
Next: Sprint 7 - Telegram Bot Integration
EOF

# Optional: Create tag
git tag -a sprint-6-complete -m "Sprint 6: WebApp Engine Power Field Integration Complete"

# Push changes
git push origin feature/specification-upgrade
git push origin sprint-6-complete  # if tagged
```

## Commit Message Breakdown

### Type: `feat`
- New feature addition (engine power field)
- Not `fix` (no bugs fixed)
- Not `refactor` (not restructuring existing code)
- Not `docs` (docs are secondary to code changes)

### Scope: `webapp`
- Changes primarily in WebApp frontend
- Alternative scopes considered:
  - `frontend` - too generic
  - `ui` - less specific
  - `form` - too narrow

### Subject Line
- Clear, concise description of what was added
- Mentions both validation AND display (dual functionality)
- Under 72 characters

### Body
- **Summary:** One-line sprint completion statement
- **Changes:** Bulleted list of all modifications
- **Integration:** Verification status with checkmarks
- **Metrics:** Files/tests/time tracking
- **References:** Links to sprint docs and next steps

### Footer
- `Refs:` Sprint prompt document
- `Next:` What comes after this sprint
- Optional: `Closes:` if using issue tracking

## Alternative Commit Strategies

### Strategy 1: Single Commit (Recommended for Sprint)
✅ **Pros:**
- Complete sprint in one logical unit
- Easy to review all changes together
- Clean history with sprint milestones

❌ **Cons:**
- Large diff size
- Harder to cherry-pick individual changes

### Strategy 2: Multiple Commits (Granular)
Could split into:
1. `feat(webapp): add engine power HTML field`
2. `feat(webapp): add engine power validation`
3. `feat(webapp): add engine power API integration`
4. `feat(webapp): add engine power result display`
5. `test(webapp): add engine power field tests`
6. `docs: update rpg.yaml for sprint 6`

✅ **Pros:**
- Easier to understand each change
- Better for bisecting bugs
- More professional commit log

❌ **Cons:**
- More work to commit separately
- Risk of incomplete intermediate states
- Sprint 6 spread across multiple commits

### Strategy 3: Squash on Merge (Best of Both)
- Commit granularly during development
- Squash into single commit on merge to main
- Preserves detailed history in feature branch

## Branch Strategy

### Current Branch
```bash
git branch  # should show: feature/specification-upgrade
```

### Merge Options

**Option A: Direct Merge**
```bash
git checkout main
git merge --no-ff feature/specification-upgrade -m "Merge Sprint 6: Engine Power Field"
```

**Option B: Pull Request**
```bash
# Push feature branch
git push origin feature/specification-upgrade

# Create PR on GitHub/GitLab
# Title: "Sprint 6: Engine Power Field Integration"
# Description: Link to SPRINT_6_SUMMARY.md
```

**Option C: Continue in Branch**
```bash
# Keep working on Sprint 7 in same branch
git checkout feature/specification-upgrade
# No merge needed yet, wait until all sprints complete
```

## Commit Verification

### Pre-commit Checks
```bash
# 1. No syntax errors
npm run lint  # if you have linter
python -m py_compile app/**/*.py

# 2. Tests pass
python -m pytest tests/
open http://localhost:8000/tests/manual/test_engine_power_field.html

# 3. No uncommitted changes
git status

# 4. Review diff
git diff --staged
```

### Post-commit Verification
```bash
# 1. Commit created
git log -1 --stat

# 2. Changes included
git show HEAD --name-only

# 3. Tag created (if tagged)
git tag -l sprint-*

# 4. Remote synced (if pushed)
git log origin/feature/specification-upgrade..HEAD  # should be empty
```

## Rollback Plan

If something goes wrong:

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) - DANGEROUS
git reset --hard HEAD~1

# Undo pushed commit
git revert HEAD
git push origin feature/specification-upgrade

# Return to specific commit
git reset --hard <commit-sha>
```

## CI/CD Integration

If you have automated pipelines:

```yaml
# .github/workflows/sprint-6.yml
name: Sprint 6 Tests
on:
  push:
    paths:
      - 'app/webapp/**'
      - 'tests/manual/**'
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test Engine Power Field
        run: |
          npm test
          pytest tests/functional/test_api.py
```

## Summary

**Recommended Command:**
```bash
git add -A
git commit -m "feat(webapp): add engine_power_hp field with validation and result display

SPRINT 6 COMPLETE: All objectives achieved
- Form field with validation
- API integration verified
- Result display with conversion
- 16 tests passing

Refs: docs/sprint_prompts/SPRINT_6_FRONTEND_WEBAPP.md"
```

This keeps the commit message concise while still conveying all essential information.

