# Git Commit Message

Используй эту команду для коммита всех изменений:

```bash
git add docs/rpg.yaml docs/sprint_prompts/

git commit -m "docs(rpg): create sprint prompts 4-10 with RPG methodology

- Обновлён граф проекта (rpg.yaml) с информацией о спринтах 0-3 и промптах 4-10
- Созданы 7 промптов для спринтов 4-10 рефакторинга системы утилизации:
  - SPRINT_4: Обновление пошлин и комиссий (1-2ч)
  - SPRINT_5: API метаданные (1ч)
  - SPRINT_6: Фронтенд WebApp (3-4ч)
  - SPRINT_7: Telegram Bot (1ч)
  - SPRINT_8: Тестирование (3-4ч)
  - SPRINT_9: Документация (1-2ч)
  - SPRINT_10: Финализация и деплой (1ч)

Каждый промпт содержит:
- Роль модели для активации релевантных знаний
- Методологию RPG с ключевыми принципами
- Обязательное обновление графа проекта (rpg.yaml)
- Источники правды (первичные/вторичные)
- Решение проблемы 'Lost in the Middle' (минимизация контекста)
- Критерии достижения цели (Must/Should/Nice to Have)
- Задачи в топологическом порядке
- Тестирование (manual + automated)
- Проблемы и решения
- Требование docstrings для всех публичных функций/классов

Дополнительно созданы:
- README.md — индекс всех промптов с графом зависимостей
- SUMMARY.md — итоговый отчёт о создании промптов

Общий объём: ~3,090 строк документации
Методология: Repository Planning Graph (RPG)
Оценка времени выполнения спринтов 4-10: 12-18 часов

See: docs/sprint_prompts/README.md, docs/sprint_prompts/SUMMARY.md"
```

---

## Альтернативный вариант (краткий):

```bash
git add docs/rpg.yaml docs/sprint_prompts/

git commit -m "docs(rpg): add sprint prompts 4-10 for refactoring

Created 7 LLM-ready prompts for remaining refactoring sprints (4-10)
using RPG methodology. Each prompt solves 'Lost in the Middle' problem
with minimal context and includes role definition, success criteria,
and mandatory rpg.yaml updates.

Total: ~3k lines of documentation, 12-18h estimated work.

Files:
- docs/sprint_prompts/SPRINT_{4..10}_*.md (7 prompts)
- docs/sprint_prompts/README.md (index)
- docs/sprint_prompts/SUMMARY.md (report)
- docs/rpg.yaml (updated with sprint_prompts section)"
```

---

## После коммита:

```bash
# Проверь, что всё закоммичено
git status

# Запуш в remote (если нужно)
git push origin feature/spec-2025-utilization-upgrade

# Переходи к выполнению SPRINT 4
cat docs/sprint_prompts/SPRINT_4_DUTIES_COMMISSIONS.md
```

