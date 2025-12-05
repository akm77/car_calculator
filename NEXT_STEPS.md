# NEXT STEPS: Sprint 6 Planning

## Sprint 5 Status: ✅ ЗАВЕРШЁН

### Что сделано
- ✅ API client module (api.js) - 470 строк
- ✅ Test suite (test_api_client.html) - 574 строк, 8 тестов
- ✅ Документация (5 файлов)
- ✅ index.html обновлён (-125 строк)

### Что делать дальше

**Перед началом Sprint 6**:

1. **Закоммитить изменения**:
   ```bash
   # Используйте готовый commit message
   cat docs/SPRINT_5_GIT_COMMIT.md
   
   # Или просто:
   git add -A
   git commit -m "refactor(webapp): Sprint 5 - HTTP client with retry/timeout"
   git push
   ```

2. **Протестировать в браузере**:
   ```bash
   # Если сервер не запущен:
   python -m app.main
   
   # Открыть в браузере:
   # http://localhost:8000/tests/manual/test_api_client.html
   # http://localhost:8000/web/
   ```

3. **Проверить работу WebApp**:
   - Открыть калькулятор
   - Выбрать страну
   - Ввести данные
   - Нажать "Рассчитать"
   - Проверить, что ошибки обрабатываются понятно

---

## Sprint 6: UI Module

### Цель
Извлечь UI логику из index.html в отдельный модуль для улучшения читаемости и переиспользуемости.

### Задачи

#### 1. Создать `app/webapp/js/modules/ui.js`
```javascript
export class UIManager {
    // Loading state
    showLoading(show, message)
    
    // Error display
    showError(message, type)
    hideError()
    
    // Result display
    showResult()
    hideResult()
    
    // Tab management
    showCalcTab()
    showResultsTab()
    
    // Field highlighting
    highlightField(fieldId, isError)
    
    // Toast notifications
    showToast(message, type, duration)
}

export const ui = new UIManager();
```

#### 2. Обновить `index.html`
- Импортировать ui.js
- Заменить прямые манипуляции DOM на ui методы
- Удалить функции: showLoading, showError, hideError, showResult, hideResult

#### 3. Создать `tests/manual/test_ui.html`
- Тесты для всех UI методов
- Visual regression tests
- Animation tests

### Ожидаемый результат
- Удалить ~100 строк из index.html
- Создать ui.js (~200 строк)
- Создать test_ui.html (~400 строк)
- Улучшить читаемость кода

### Время
2-3 часа

---

## Sprint 7: Results Renderer

### Цель
Извлечь логику отображения результатов в отдельный модуль.

### Задачи

#### 1. Создать `app/webapp/js/modules/results.js`
```javascript
export class ResultsRenderer {
    // Main rendering
    render(result)
    
    // Breakdown items
    renderBreakdown(breakdown)
    
    // Meta info
    renderMetaInfo(meta)
    
    // Warnings
    renderWarnings(warnings)
    
    // Share functionality
    generateShareText(result)
    shareResult(result)
}

export const resultsRenderer = new ResultsRenderer();
```

#### 2. Обновить `index.html`
- Заменить displayResult() на resultsRenderer.render()
- Удалить inline функции рендеринга

### Ожидаемый результат
- Удалить ~150 строк из index.html
- Создать results.js (~250 строк)

### Время
2-3 часа

---

## Sprint 8: Calculator Controller

### Цель
Создать контроллер для оркестрации всех модулей.

### Задачи

#### 1. Создать `app/webapp/js/modules/calculator.js`
```javascript
export class CalculatorController {
    constructor(api, ui, validator, resultsRenderer)
    
    // Main flow
    async calculate(formData)
    
    // Initialization
    init()
    setupEventListeners()
    
    // Country/freight selection
    selectCountry(country)
    selectFreightType(type)
}

export const calculator = new CalculatorController(api, ui, validator, resultsRenderer);
```

#### 2. Обновить `index.html`
- Заменить inline event handlers на calculator методы
- Удалить функции: calculateCost, selectCountry, etc.

### Ожидаемый результат
- Удалить ~200 строк из index.html
- Создать calculator.js (~300 строк)

### Время
3-4 часа

---

## Sprint 9: Minimal index.html

### Цель
Оставить в index.html только HTML структуру и минимальный инициализационный код.

### Результат
```html
<!DOCTYPE html>
<html>
<head>
    <!-- CSS -->
    <link rel="stylesheet" href="/static/css/variables.css">
    <!-- ... -->
</head>
<body>
    <!-- HTML structure only -->
    <div class="container">
        <!-- ... -->
    </div>
    
    <script type="module">
        import { calculator } from '/static/js/modules/calculator.js';
        calculator.init();
    </script>
</body>
</html>
```

### Ожидаемый размер
- index.html: ~300 строк (было 1548)
- Reduction: ~80% меньше кода

### Время
1-2 часа

---

## Общий прогресс рефакторинга

### Завершено (Sprints 0-5)
- ✅ Sprint 0: Структура папок
- ✅ Sprint 1: CSS extraction (4 файла)
- ✅ Sprint 2: Utils (formatters.js, dom.js)
- ✅ Sprint 3: Config (messages.js, constants.js)
- ✅ Sprint 4: Validator (validator.js)
- ✅ Sprint 5: API client (api.js) ← **ТЕКУЩИЙ**

### Осталось (Sprints 6-9)
- ⏳ Sprint 6: UI module (ui.js)
- ⏳ Sprint 7: Results renderer (results.js)
- ⏳ Sprint 8: Calculator controller (calculator.js)
- ⏳ Sprint 9: Minimal index.html

### Timeline
- Спринты 0-5: ~12 часов (DONE)
- Спринты 6-9: ~10 часов (PLANNED)
- **Total**: ~22 часа рефакторинга

---

## Quick Start для Sprint 6

```bash
# 1. Закоммитить Sprint 5
git add -A
git commit -m "refactor(webapp): Sprint 5 - API client"

# 2. Создать файл
touch app/webapp/js/modules/ui.js

# 3. Прочитать план
cat docs/webapp_refactoring_plan.md | grep -A 30 "Этап 6"

# 4. Начать работу
code app/webapp/js/modules/ui.js
```

---

## Resources

### Документация
- `docs/webapp_refactoring_plan.md` - План всех этапов
- `docs/webapp_refactoring_checklist.md` - Чеклист прогресса
- `docs/SPRINT_5_COMPLETED.md` - Детали Sprint 5
- `docs/rpg.yaml` - Архитектура проекта

### Тесты
- `tests/manual/test_api_client.html` - API тесты
- `tests/manual/test_validator.html` - Validator тесты
- `tests/manual/test_formatters.html` - Formatter тесты

### Модули (созданы)
- `app/webapp/js/modules/api.js` (470 строк) ✅
- `app/webapp/js/modules/validator.js` (252 строк) ✅
- `app/webapp/js/config/constants.js` (185 строк) ✅
- `app/webapp/js/config/messages.js` (380 строк) ✅
- `app/webapp/js/utils/formatters.js` (330 строк) ✅
- `app/webapp/js/utils/dom.js` (250 строк) ✅

### Модули (планируются)
- `app/webapp/js/modules/ui.js` - Sprint 6
- `app/webapp/js/modules/results.js` - Sprint 7
- `app/webapp/js/modules/calculator.js` - Sprint 8

---

## Questions?

- Прочитайте `docs/webapp_refactoring_plan.md`
- Посмотрите completed sprints: `docs/SPRINT_*_COMPLETED.md`
- Проверьте rpg.yaml: `cat docs/rpg.yaml`

**Готов к Sprint 6!** 🚀

