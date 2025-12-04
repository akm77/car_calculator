# WebApp JavaScript Modules Structure

## Архитектура

Модульная структура на vanilla JavaScript с ES6 модулями для расчёта стоимости ввоза автомобилей.

**Принципы:**
- ✅ Vanilla JS + ES6 модули (без фреймворков)
- ✅ Разделение ответственности (SoC)
- ✅ Каждый модуль < 300 строк
- ✅ Явные зависимости через import/export
- ❌ Без оверинжиниринга

## Структура папок

```
js/
├── config/          # Конфигурация и константы
│   ├── constants.js # API endpoints, границы валидации, опции
│   └── messages.js  # Текстовые сообщения (ошибки, предупреждения, labels)
│
├── utils/           # Утилиты общего назначения
│   ├── formatters.js # Форматирование чисел, валют, дат
│   ├── dom.js       # DOM helpers (show, hide, getValue, setValue)
│   └── debounce.js  # Debounce для оптимизации событий
│
└── modules/         # Бизнес-логика приложения
    ├── validator.js    # Валидация формы (возраст, объём, цена)
    ├── api.js          # HTTP клиент для /api/* (fetch с retry, timeout)
    ├── ui.js           # Управление UI (показ/скрытие секций, loading states)
    ├── results.js      # Рендеринг результатов расчёта
    └── calculator.js   # Главный контроллер (оркестрация всех модулей)
```

## Зависимости модулей (топологический порядок)

```
Уровень 0 (без зависимостей):
  - config/constants.js
  - config/messages.js
  - utils/formatters.js
  - utils/dom.js
  - utils/debounce.js

Уровень 1 (зависят от уровня 0):
  - modules/validator.js    → config/*, utils/formatters
  - modules/api.js          → config/constants
  - modules/ui.js           → utils/dom

Уровень 2 (зависят от уровня 1):
  - modules/results.js      → utils/formatters, utils/dom, config/messages

Уровень 3 (зависят от уровня 2):
  - modules/calculator.js   → modules/*, utils/*, config/*
```

## Граф потоков данных

```
User Input (Form)
      ↓
calculator.js (orchestrator)
      ↓
validator.js → Validation Rules (config/constants)
      ↓
api.js → POST /api/calculate
      ↓
results.js → Format & Display
      ↓
ui.js → Show/Hide Sections
```

## Точка входа

`index.html` загружает только `modules/calculator.js` как ES6 модуль:

```html
<script type="module">
  import { initCalculator } from '/static/js/modules/calculator.js';
  initCalculator();
</script>
```

## Инициализация

1. `calculator.js` импортирует все зависимости
2. Регистрирует обработчики событий
3. Загружает мета-данные из `/api/meta` (список стран)
4. Заполняет селекты динамически
5. Готов к расчётам

## Расширение функциональности

### Добавление новой страны (30 мин):
1. Добавить конфиг в `config/*.yml` (backend)
2. Страна автоматически появится в UI через `/api/meta`
3. Никаких изменений в JS коде не требуется ✅

### Добавление нового поля формы:
1. Добавить HTML элемент в `index.html`
2. Добавить валидацию в `validator.js`
3. Добавить обработку в `calculator.js`
4. Обновить `api.js` если нужны новые параметры

### Добавление нового формата вывода:
1. Добавить функцию в `formatters.js`
2. Использовать в `results.js`

## Тестирование

### Manual Testing:
- Открыть `/web/` в браузере
- Проверить консоль на ошибки
- Заполнить форму и проверить расчёт
- Проверить все country options

### Browser DevTools:
```javascript
// Проверить что модули загружены
console.log(window.performance.getEntriesByType('resource')
  .filter(r => r.name.includes('/static/js/')));
```

## Performance

### Преимущества модульной структуры:
- **Браузерное кэширование**: CSS/JS файлы кэшируются отдельно
- **Параллельная загрузка**: Браузер загружает модули параллельно
- **Tree shaking**: Неиспользуемый код не загружается (при использовании bundler)
- **Читаемость**: Легко найти нужный код

### Размеры модулей (целевые):
- `constants.js`: ~50 строк
- `messages.js`: ~100 строк
- `formatters.js`: ~100 строк
- `dom.js`: ~50 строк
- `debounce.js`: ~20 строк
- `validator.js`: ~150 строк
- `api.js`: ~150 строк
- `ui.js`: ~100 строк
- `results.js`: ~200 строк
- `calculator.js`: ~250 строк

**Total**: ~1170 строк (vs 1548 строк монолита)
**Reduction**: ~24% + лучшая организация

## Changelog

- **2025-12-05**: СПРИНТ 0 - Создана базовая структура папок
- **2025-12-05**: Создан README.md с описанием архитектуры

## Next Steps

См. `docs/webapp_refactoring_plan.md` для детального плана следующих этапов:
- Этап 1: Вынос CSS (2-3 часа)
- Этап 2: Вынос утилит (3-4 часа)
- Этап 3: Вынос конфигурации (2 часа)
- И далее...

