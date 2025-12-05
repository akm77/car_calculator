# Git Commit Guide for Sprint 6

## Files to commit

### New files (3):
```bash
git add app/webapp/js/modules/ui.js
git add tests/manual/test_ui_module.html
git add docs/SPRINT_6_COMPLETED.md
```

### Modified files (5):
```bash
git add app/webapp/index.html
git add app/webapp/css/components.css
git add docs/rpg.yaml
git add docs/webapp_refactoring_checklist.md
git add CHANGELOG_georgia.md
```

## Commit command

```bash
git commit -m "refactor(webapp): SPRINT 6 - централизованный UI менеджер с state management

Создан модуль ui.js (380 строк) с классом UI:
- State management: idle/loading/error/success FSM
- Методы: showLoading/showError/showResult/hideResult/showToast
- Анимации: fade-in/fade-out (CSS transitions 300ms)
- Telegram: haptic feedback (light/medium/heavy)
- Accessibility: ARIA атрибуты, focus management

Рефакторинг index.html (-130 строк):
- Удалены старые UI функции (showError/showLoading/hideResult/showToast)
- Заменены 18 вызовов на ui.* методы
- Добавлен импорт ui модуля

CSS анимации (+45 строк):
- @keyframes slideUp/slideDown
- .toast стили

Тесты (+460 строк):
- tests/manual/test_ui_module.html
- 8 секций, 30+ тестов
- Interactive UI с pass/fail индикаторами

Документация:
- docs/rpg.yaml: добавлен UI компонент
- docs/webapp_refactoring_checklist.md: Этап 6 ✅
- CHANGELOG_georgia.md: полная запись Sprint 6
- docs/SPRINT_6_COMPLETED.md: итоговый отчёт

Метрики:
- index.html: -130 строк
- Новые файлы: +1285 строк
- Чистый прирост: +1155 строк (better organized)

Closes #SPRINT_6
"
```

## Verify before commit

```bash
# Check status
git status

# Review changes
git diff app/webapp/index.html
git diff app/webapp/css/components.css

# Check new files
cat app/webapp/js/modules/ui.js | head -50
cat tests/manual/test_ui_module.html | head -50
```

## Push to remote

```bash
git push origin main
```

---

**Ready to commit!** ✅

