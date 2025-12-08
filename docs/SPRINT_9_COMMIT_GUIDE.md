# Sprint 9 Commit Guide

**Спринт:** 9 - Documentation Finalization (v2.0)  
**Дата:** 8 декабря 2025

---

## 📋 Файлы для коммита

### Созданные файлы
```bash
docs/MIGRATION_GUIDE.md
docs/SPRINT_9_SUMMARY.md
docs/SPRINT_9_COMMIT_GUIDE.md
```

### Изменённые файлы
```bash
docs/SPECIFICATION.md
CHANGELOG.md
docs/rpg.yaml
docs/API_RESULT_FLOW.md
```

---

## 🔍 Проверка перед коммитом

### 1. Проверка статуса Git
```bash
cd /Users/admin/PycharmProjects/car_calculator
git status
```

**Ожидаемый вывод:**
```
On branch main
Changes not staged for commit:
  modified:   CHANGELOG.md
  modified:   docs/API_RESULT_FLOW.md
  modified:   docs/SPECIFICATION.md
  modified:   docs/rpg.yaml

Untracked files:
  docs/MIGRATION_GUIDE.md
  docs/SPRINT_9_SUMMARY.md
  docs/SPRINT_9_COMMIT_GUIDE.md
```

### 2. Проверка изменений
```bash
# Посмотреть изменения в SPECIFICATION.md
git diff docs/SPECIFICATION.md | head -50

# Посмотреть изменения в CHANGELOG.md
git diff CHANGELOG.md | head -100

# Посмотреть изменения в rpg.yaml
git diff docs/rpg.yaml | head -50
```

---

## 💾 Последовательность коммитов

### Коммит 1: Обновление SPECIFICATION.md
```bash
git add docs/SPECIFICATION.md

git commit -m "docs(spec): add v2.0 implementation markers

- Add '✅ Статус: Реализовано в v2.0' markers to:
  - Классификация автомобилей
  - Утилизационный сбор (с описанием новой 2D системы)
  - Таможенная пошлина
  - ЭРА-ГЛОНАСС (45,000 руб.)
  - Комиссия компании (фиксированная 1000 USD)
- Add config file references (rates.yml, commissions.yml)
- Update utilization fee section with algorithm details

Related: Sprint 9, Task 9.1
Ref: docs/REFACTORING_PLAN.md (Этап 9)"
```

### Коммит 2: Создание MIGRATION_GUIDE.md
```bash
git add docs/MIGRATION_GUIDE.md

git commit -m "docs: add comprehensive migration guide for v2.0

- Create MIGRATION_GUIDE.md with full migration instructions
- Document breaking changes (engine_power_hp required field)
- Add code examples for Python, JavaScript, cURL
- Include migration checklists for Backend/Frontend/DevOps
- Add rollback plan (3-step: config, code, database)
- Add FAQ section (7 Q&A)
- Add support contacts and cross-references

Breaking Changes:
- POST /api/calculate now requires engine_power_hp (1-1500)
- Response meta includes engine_power_hp, engine_power_kw, utilization_coefficient
- Utilization fee calculation changed (2D table)
- Commission changed to fixed 1000 USD

Related: Sprint 9, Task 9.2
Ref: docs/REFACTORING_PLAN.md (Этап 9)"
```

### Коммит 3: Обновление CHANGELOG.md
```bash
git add CHANGELOG.md

git commit -m "docs(changelog): add v2.0.0 release notes

- Add v2.0.0 section with full changelog (2025-12-08)
- Document Added features (new utilization system, API fields, WebApp, tests)
- Document Changed features (utilization, commission, tariffs, config)
- Document Removed features (old utilization, commission gradation)
- Document Breaking Changes (3 major incompatibilities)
- Add migration path checklist
- Add statistics (41 tests passed, 87% coverage, 25+ files changed)

Categories:
- 🚀 Added: New 2D utilization system, engine_power_hp field
- 🔄 Changed: Fixed 1000 USD commission, ERA-GLONASS 45,000 RUB
- 🗑️ Removed: Old utilization system, commission thresholds
- 🐛 Fixed: Utilization accuracy, commission consistency
- 📚 Documentation: MIGRATION_GUIDE, updated SPEC, rpg.yaml
- ⚠️ Breaking Changes: Required engine_power_hp, changed values

Related: Sprint 9, Task 9.3
Ref: docs/REFACTORING_PLAN.md (Этап 9)"
```

### Коммит 4: Финализация rpg.yaml
```bash
git add docs/rpg.yaml

git commit -m "docs(rpg): finalize project graph for v2.0.0

- Update metadata.version to 2.0.0
- Update metadata.last_updated to 2025-12-08
- Add Sprint 9 to recent_changes (documentation finalization)
- Update module descriptions:
  - engine.py: mention _utilization_fee_v2
  - models.py: add engine_power_hp/kw/coefficient fields
  - commissions.yml: new structure (fixed 1000 USD)
  - rates.yml: utilization_m1_personal + era_glonass_rub
- Add _utilization_fee_v2 component with detailed description
- Mark _utilization_fee as DEPRECATED
- Update test_status: 41 passed, 87% coverage, v2.0.0 released

Related: Sprint 9, Task 9.4
Ref: docs/REFACTORING_PLAN.md (Этап 9)"
```

### Коммит 5: Обновление API_RESULT_FLOW.md
```bash
git add docs/API_RESULT_FLOW.md

git commit -m "docs(api): update API flow documentation for v2.0

- Update date to '8 декабря 2025 (обновлено для v2.0)'
- Add v2.0 warning note with MIGRATION_GUIDE.md link
- Add engine_power_hp to request data examples
- Add new meta fields:
  - engine_power_hp: 110 (original horsepower)
  - engine_power_kw: 80.91 (converted to kW)
  - utilization_coefficient: 0.26 (table coefficient)
- Mark engine_power_hp as REQUIRED field in request section

Related: Sprint 9, Task 9.5
Ref: docs/REFACTORING_PLAN.md (Этап 9)"
```

### Коммит 6: Добавление итоговых документов спринта
```bash
git add docs/SPRINT_9_SUMMARY.md docs/SPRINT_9_COMMIT_GUIDE.md

git commit -m "docs(sprint9): add sprint summary and commit guide

- Add SPRINT_9_SUMMARY.md with complete sprint report:
  - All 5 tasks completed (9.1-9.5)
  - Statistics: 1 file created, 4 files updated, ~500 lines added
  - Quality checklist: completeness, accuracy, readability, navigation
- Add SPRINT_9_COMMIT_GUIDE.md with commit instructions
- Document final status: v2.0.0 documentation complete

Sprint 9 Status: ✅ COMPLETED
Next: Sprint 10 (Finalization)

Related: Sprint 9
Ref: docs/REFACTORING_PLAN.md (Этап 9)"
```

---

## 🎯 Единый коммит (альтернатива)

Если предпочитаете один коммит:

```bash
git add docs/SPECIFICATION.md \
        CHANGELOG.md \
        docs/rpg.yaml \
        docs/API_RESULT_FLOW.md \
        docs/MIGRATION_GUIDE.md \
        docs/SPRINT_9_SUMMARY.md \
        docs/SPRINT_9_COMMIT_GUIDE.md

git commit -m "docs: complete Sprint 9 - v2.0 documentation finalization

SPRINT 9 COMPLETED: Actualized all project documentation after new utilization system implementation

Created files:
- docs/MIGRATION_GUIDE.md: comprehensive v1.x→v2.0 migration guide
- docs/SPRINT_9_SUMMARY.md: sprint completion report
- docs/SPRINT_9_COMMIT_GUIDE.md: commit instructions

Updated files:
- docs/SPECIFICATION.md: added v2.0 implementation markers for all sections
- CHANGELOG.md: full v2.0.0 release notes with breaking changes
- docs/rpg.yaml: finalized project graph (version 2.0.0, all sprints 0-9)
- docs/API_RESULT_FLOW.md: updated with engine_power_hp examples

Key changes:
✅ SPECIFICATION.md: 5 sections marked as 'Реализовано в v2.0'
✅ MIGRATION_GUIDE.md: 380 lines, Python/JS/cURL examples, rollback plan, FAQ
✅ CHANGELOG.md: v2.0.0 section with Added/Changed/Removed/Breaking/Stats
✅ rpg.yaml: version 2.0.0, Sprint 9 in recent_changes, updated components
✅ API_RESULT_FLOW.md: engine_power_hp in request/response examples

Breaking changes documented:
- engine_power_hp is now REQUIRED (1-1500 HP)
- Utilization fee calculation changed (2D table)
- Commission changed to fixed 1000 USD
- Response meta includes new fields (engine_power_hp, engine_power_kw, utilization_coefficient)

Statistics:
- Files created: 1 (MIGRATION_GUIDE.md)
- Files updated: 4
- Lines added: ~500
- Coverage: 87%
- Tests: 41 passed

Sprint 9 Status: ✅ COMPLETED
Project Version: 2.0.0
Date: 2025-12-08

Related: Sprint 9 (Tasks 9.1-9.5)
Ref: docs/REFACTORING_PLAN.md (Этап 9)
Next: Sprint 10 (Finalization)"
```

---

## ✅ Проверка после коммита

### 1. Проверка истории
```bash
git log --oneline -7
```

**Ожидаемый вывод:**
```
abc1234 docs: complete Sprint 9 - v2.0 documentation finalization
...
```

### 2. Проверка файлов в коммите
```bash
git show --name-only HEAD
```

**Ожидаемые файлы:**
- docs/SPECIFICATION.md
- CHANGELOG.md
- docs/rpg.yaml
- docs/API_RESULT_FLOW.md
- docs/MIGRATION_GUIDE.md
- docs/SPRINT_9_SUMMARY.md
- docs/SPRINT_9_COMMIT_GUIDE.md

### 3. Проверка изменений
```bash
# Посмотреть полный diff последнего коммита
git show HEAD

# Или только статистику
git show --stat HEAD
```

---

## 🚀 Push в удалённый репозиторий

```bash
# Проверка remote
git remote -v

# Push в main branch
git push origin main

# Или если используете другую ветку
git push origin <branch-name>
```

---

## 🏷️ Создание тега v2.0.0 (опционально)

```bash
# Создание аннотированного тега
git tag -a v2.0.0 -m "Release v2.0.0: New utilization system with 2D table

Major changes:
- New 2D utilization fee system (volume + power)
- Required engine_power_hp field (1-1500 HP)
- Fixed commission: 1000 USD
- ERA-GLONASS: 45,000 RUB
- Updated duties (lt3: 6 brackets)

Breaking changes:
- API requires engine_power_hp
- Utilization calculation changed
- Commission formula changed

Documentation:
- Complete MIGRATION_GUIDE.md
- Updated SPECIFICATION.md
- Full CHANGELOG.md v2.0.0

Tests: 41 passed, 87% coverage
Date: 2025-12-08"

# Push тега
git push origin v2.0.0

# Или все теги
git push origin --tags
```

---

## 📊 Итоговая проверка

### Checklist
- [ ] Все файлы добавлены в коммит
- [ ] Коммит-сообщение информативное
- [ ] История коммитов чистая
- [ ] Push выполнен успешно
- [ ] Тег v2.0.0 создан (опционально)
- [ ] Документация доступна в репозитории

### Следующие шаги
1. ✅ Sprint 9 завершён
2. → Переход к Sprint 10 (Finalization)
3. → Проверка README.md
4. → Финальный релиз

---

**Дата:** 8 декабря 2025  
**Версия:** 2.0.0  
**Статус:** ✅ READY TO COMMIT

