# WebApp Refactoring - Спринты по методике RPG

> Разбивка плана рефакторинга на спринты с учётом ограничений контекста модели и проблемы "lost in the middle"

## Принципы разбиения на спринты

1. **Размер спринта**: Каждый спринт должен укладываться в ~3000 токенов контекста
2. **Автономность**: Спринт должен давать работающий результат
3. **Топологический порядок**: От фундамента (utils) к надстройкам (controller)
4. **Простота**: Избегаем оверинжиниринга
5. **Инкрементальность**: Проверка работоспособности после каждого спринта

---

## СПРИНТ 0: Подготовка инфраструктуры

**Длительность**: 1-2 часа  
**Сложность**: Низкая  
**Зависимости**: Нет

### Роль модели
Ты — инфраструктурный инженер, создающий базовую структуру для модульного фронтенд приложения на vanilla JavaScript с ES6 модулями.

### Источники правды
- `docs/webapp_refactoring_plan.md` - общий план (Этап 0)
- `docs/rpg.yaml` - граф проекта (раздел app_webapp)
- `app/webapp/index.html` - текущее монолитное состояние (для понимания)

### Задачи спринта
1. Создать структуру папок:
   ```
   app/webapp/js/config/
   app/webapp/js/utils/
   app/webapp/js/modules/
   app/webapp/css/
   ```

2. Создать файл бэкапа:
   ```bash
   cp app/webapp/index.html app/webapp/index.html.backup
   ```

3. Создать `.gitignore` для `app/webapp/`:
   ```
   *.backup
   node_modules/
   .DS_Store
   ```

4. Создать `app/webapp/js/README.md` с описанием структуры модулей

5. Обновить `app/main.py` для раздачи новых статических файлов (`/static/css/`, `/static/js/`)

### Критерии достижения цели
- ✅ Все папки созданы
- ✅ Бэкап index.html существует
- ✅ FastAPI раздаёт статику из новых папок (проверить `/static/css/test.css`)
- ✅ Нет ошибок в терминале при запуске `python -m app.main`

### Обновление документации
После завершения обнови:
- `docs/rpg.yaml` - добавить в узел `app_webapp` информацию о новой структуре
- `CHANGELOG_georgia.md` - новая запись о начале рефакторинга

---

## СПРИНТ 1: Извлечение CSS

**Длительность**: 2-3 часа  
**Сложность**: Низкая  
**Зависимости**: Спринт 0

### Роль модели
Ты — CSS-архитектор, разделяющий монолитные стили на логические модули с использованием CSS переменных и БЭМ-подобной методологии.

### Источники правды
- `app/webapp/index.html` (строки 1-300) - секция `<style>` с CSS
- `docs/webapp_refactoring_plan.md` - Этап 1
- Telegram Design Guidelines для стилей (используй `var(--tg-theme-*)`)

### Задачи спринта
1. Создать `app/webapp/css/variables.css`:
   - CSS-переменные для цветов (Telegram theme colors)
   - Переменные для размеров (шрифты, отступы, радиусы)
   - Переменные для брейкпоинтов (если есть)

2. Создать `app/webapp/css/base.css`:
   - CSS reset/normalize
   - Базовые стили body, html
   - Стили контейнера `.container`
   - Типографика (h1, h2, p)

3. Создать `app/webapp/css/components.css`:
   - Кнопки (`.btn`, `.btn-primary`, `.btn-telegram`)
   - Карточки (`.card`, `.result-card`)
   - Формы (`.form-group`, `.input`, `.select`)
   - Breakdown items (`.breakdown-item`)

4. Создать `app/webapp/css/telegram.css`:
   - Telegram WebApp специфичные стили
   - Адаптация под тёмную тему
   - Стили для кнопок-переключателей

5. Обновить `app/webapp/index.html`:
   - Удалить `<style>...</style>`
   - Добавить `<link>` на все 4 CSS файла

### Критерии достижения цели
- ✅ В index.html нет тега `<style>`
- ✅ Все 4 CSS файла подключены через `<link>`
- ✅ WebApp открывается без визуальных изменений
- ✅ Нет ошибок в консоли браузера (F12)
- ✅ Работает переключение тёмной темы в Telegram

### Обновление документации
После завершения обнови:
- `docs/webapp_refactoring_checklist.md` - отметить Этап 1 выполненным
- `CHANGELOG_georgia.md` - запись о выносе CSS

---

## СПРИНТ 2: Утилиты форматирования и DOM

**Длительность**: 3-4 часа  
**Сложность**: Средняя  
**Зависимости**: Спринт 1

### Роль модели
Ты — разработчик библиотеки утилит, создающий чистые функции (pure functions) для форматирования данных и работы с DOM без зависимостей от внешних библиотек.

### Источники правды
- `app/webapp/index.html` (строки 300-800) - функции `formatNumber()`, `show()`, `hide()`, etc.
- `docs/webapp_refactoring_plan.md` - Этап 2
- `docs/rpg.yaml` - модуль `app_calculation/models.py` для понимания типов данных

### Задачи спринта

1. Создать `app/webapp/js/utils/formatters.js`:
   ```javascript
   // Экспорт:
   // - formatNumber(num) → строка с разделителями
   // - formatCurrency(amount, currency) → форматированная валюта
   // - getAgeCategory(category) → человекочитаемая метка
   // - formatEngineVolume(cc) → "1500 см³"
   // - formatYear(year) → проверка и форматирование
   ```

2. Создать `app/webapp/js/utils/dom.js`:
   ```javascript
   // Экспорт:
   // - show(element) → добавить класс .show
   // - hide(element) → убрать класс .show
   // - setContent(elementId, html) → innerHTML
   // - setText(elementId, text) → textContent
   // - debounce(fn, delay) → дебаунс функция
   // - throttle(fn, delay) → троттлинг (для scroll/resize)
   ```

3. Обновить `app/webapp/index.html`:
   - Добавить `<script type="module">` импорты
   - Заменить прямые вызовы на импортированные функции
   - Убедиться что `formatNumber()` больше не объявлена в HTML

4. Создать базовый тест `tests/manual/test_formatters.html`:
   - Проверить форматирование чисел
   - Проверить форматирование валют
   - Проверить debounce/throttle

### Критерии достижения цели
- ✅ Файлы `formatters.js` и `dom.js` содержат только чистые функции
- ✅ В `index.html` нет дублирования этих функций
- ✅ WebApp работает без изменений в поведении
- ✅ Открыть `tests/manual/test_formatters.html` - все тесты проходят (✅)
- ✅ Нет ошибок импорта модулей в консоли

### Обновление документации
После завершения обнови:
- `docs/rpg.yaml` - добавить компоненты `formatters.js` и `dom.js`
- `docs/webapp_refactoring_checklist.md` - отметить Этап 2
- `CHANGELOG_georgia.md` - запись о создании утилит

---

## СПРИНТ 3: Константы и конфигурация

**Длительность**: 1-2 часа  
**Сложность**: Низкая  
**Зависимости**: Спринт 2

### Роль модели
Ты — конфигурационный менеджер, выделяющий все магические числа, строки и настройки в единые источники правды для упрощения поддержки и локализации.

### Источники правды
- `app/webapp/index.html` (строки 800-1200) - хардкод строк и чисел
- `app/calculation/models.py` - константы валидации (MIN_YEAR, MAX_CC, etc.)
- `docs/webapp_refactoring_plan.md` - Этап 3
- `app/core/messages.py` - серверные сообщения (для согласованности)

### Задачи спринта

1. Создать `app/webapp/js/config/messages.js`:
   ```javascript
   // Экспорт объекта Messages с разделами:
   // - errors: тексты ошибок валидации
   // - buttons: тексты кнопок
   // - labels: метки полей
   // - info: информационные сообщения
   // - warnings: предупреждения
   ```

2. Создать `app/webapp/js/config/constants.js`:
   ```javascript
   // Экспорт:
   // - Constraints: лимиты валидации (YEAR_MIN, YEAR_MAX, ENGINE_CC_MIN, etc.)
   // - API_ENDPOINTS: пути к API (/api/calculate, /api/meta, etc.)
   // - API_CONFIG: retry, timeout, delay
   // - DEFAULT_VALUES: дефолты для формы (freight_type, vehicle_type, etc.)
   // - COUNTRY_EMOJI: эмодзи стран (fallback если API не вернёт)
   ```

3. Синхронизировать константы с бэкендом:
   - Импортировать значения из `app/calculation/models.py` (через комментарии)
   - Убедиться что MIN_YEAR, MAX_CC совпадают с серверной валидацией

4. Обновить `app/webapp/index.html`:
   - Импортировать Messages и Constants
   - Заменить все хардкод строки на `Messages.errors.NO_COUNTRY`, etc.
   - Заменить магические числа на `Constraints.YEAR_MIN`, etc.

### Критерии достижения цели
- ✅ В `index.html` нет строковых литералов для UI текстов
- ✅ В `index.html` нет магических чисел для валидации
- ✅ Константы валидации совпадают с `app/calculation/models.py`
- ✅ WebApp показывает те же тексты что и раньше
- ✅ Легко поменять текст кнопки (1 файл, 1 строка)

### Обновление документации
После завершения обнови:
- `docs/rpg.yaml` - добавить узлы `messages.js` и `constants.js`
- `docs/webapp_refactoring_checklist.md` - отметить Этап 3
- `CHANGELOG_georgia.md` - запись о выделении констант

---

## СПРИНТ 4: Модуль валидации форм

**Длительность**: 2-3 часа  
**Сложность**: Средняя  
**Зависимости**: Спринт 3

### Роль модели
Ты — инженер по валидации данных, создающий единый модуль валидации форм с поддержкой как полной валидации формы, так и валидации отдельных полей в реальном времени.

### Источники правды
- `app/webapp/index.html` (строки 900-1100) - функция `validateForm()`
- `app/calculation/models.py` - класс `CalculationRequest` с валидацией Pydantic
- `docs/webapp_refactoring_plan.md` - Этап 4
- `app/webapp/js/config/constants.js` - константы лимитов (из Спринта 3)

### Задачи спринта

1. Создать `app/webapp/js/modules/validator.js`:
   ```javascript
   // Экспорт класса FormValidator с методами:
   // - validate(formData) → {isValid: bool, errors: string[]}
   // - validateField(name, value) → string | null (ошибка или null)
   // - getFieldConstraints(name) → {min, max, pattern, required}
   ```

2. Реализовать правила валидации:
   - **year**: `YEAR_MIN <= year <= YEAR_MAX()`
   - **engine_cc**: `ENGINE_CC_MIN <= cc <= ENGINE_CC_MAX`
   - **purchase_price**: `price > 0`
   - **country**: не пустое значение
   - **currency**: валидный код (USD, EUR, JPY, CNY, AED, RUB)

3. Добавить поддержку кастомных валидаторов:
   - Метод `addCustomValidator(fieldName, validatorFn)`
   - Возможность расширения без изменения класса

4. Обновить `app/webapp/index.html`:
   - Импортировать `FormValidator`
   - Заменить `validateForm()` на `validator.validate(formData)`
   - Добавить валидацию в реальном времени на `input` события

5. Создать тест `tests/manual/test_validator.html`:
   - Валидные данные должны проходить
   - Невалидные данные должны возвращать ошибки
   - Проверить каждое правило отдельно

### Критерии достижения цели
- ✅ Класс `FormValidator` работает изолированно (можно импортировать и протестировать)
- ✅ Валидация в `index.html` использует `FormValidator`
- ✅ Валидация в реальном времени работает (поле подсвечивается при ошибке)
- ✅ Все тесты в `test_validator.html` проходят
- ✅ Нет дублирования правил валидации

### Обновление документации
После завершения обнови:
- `docs/rpg.yaml` - добавить компонент `FormValidator` с тестируемостью
- `docs/webapp_refactoring_checklist.md` - отметить Этап 4
- `CHANGELOG_georgia.md` - запись о создании модуля валидации

---

## СПРИНТ 5: Улучшенный API клиент

**Длительность**: 2-3 часа  
**Сложность**: Средняя  
**Зависимости**: Спринт 3

### Роль модели
Ты — инженер надёжности сети, создающий HTTP клиент с retry логикой, таймаутами и улучшенной обработкой ошибок для работы с нестабильными соединениями.

### Источники правды
- `app/webapp/index.html` (строки 600-800) - текущий `APIClient` класс
- `app/services/cbr.py` - пример retry логики с `@retry` декоратором
- `docs/webapp_refactoring_plan.md` - Этап 5
- `app/webapp/js/config/constants.js` - `API_CONFIG` с настройками

### Задачи спринта

1. Создать `app/webapp/js/modules/api.js`:
   ```javascript
   // Экспорт класса APIError (кастомная ошибка)
   // Экспорт класса APIClient с методами:
   // - get(path) → Promise<Response>
   // - post(path, data) → Promise<Response>
   // - fetchWithTimeout(url, options, timeout) → Promise<Response>
   // - fetchWithRetry(url, options, maxRetries) → Promise<Response>
   // 
   // Специфичные методы для нашего API:
   // - calculate(request) → Promise<CalculationResult>
   // - getMeta() → Promise<MetaData>
   // - getRates() → Promise<RatesData>
   // - refreshRates() → Promise<void>
   ```

2. Реализовать retry логику:
   - Retry только на **сетевых ошибках** (не на 4xx/5xx)
   - Экспоненциальная задержка: `delay * attempt`
   - Максимум попыток из `API_CONFIG.RETRY_COUNT`

3. Реализовать таймауты:
   - Использовать `AbortController`
   - Таймаут из `API_CONFIG.TIMEOUT` (30 секунд)
   - Выбрасывать `APIError` с кодом 408

4. Улучшить обработку ошибок:
   - Парсить JSON ошибки от FastAPI (`{"detail": "..."}`)
   - Разные типы ошибок: NetworkError, TimeoutError, ValidationError
   - Логирование в консоль (с timestamp)

5. Обновить `app/webapp/index.html`:
   - Заменить старый `APIClient` на импорт из модуля
   - Обработать `APIError` в UI (показать пользователю)

### Критерии достижения цели
- ✅ `APIClient` работает изолированно
- ✅ Retry срабатывает на сетевых ошибках (проверить через Network throttling в DevTools)
- ✅ Timeout срабатывает при медленном соединении (проверить через DevTools)
- ✅ Ошибки 4xx возвращают понятные сообщения пользователю
- ✅ WebApp корректно обрабатывает все типы ошибок

### Обновление документации
После завершения обнови:
- `docs/rpg.yaml` - обновить описание компонента `APIClient`
- `docs/webapp_refactoring_checklist.md` - отметить Этап 5
- `CHANGELOG_georgia.md` - запись об улучшении API клиента

---

## СПРИНТ 6: Модуль управления UI

**Длительность**: 3-4 часа  
**Сложность**: Средняя  
**Зависимости**: Спринты 2, 3

### Роль модели
Ты — UI инженер, создающий абстракцию над DOM манипуляциями для централизованного управления состояниями интерфейса (loading, error, success, etc.).

### Источники правды
- `app/webapp/index.html` (строки 1000-1300) - функции `showError()`, `showLoading()`, `showResult()`
- `docs/webapp_refactoring_plan.md` - Этап 6
- `app/webapp/js/utils/dom.js` - базовые DOM утилиты (из Спринта 2)

### Задачи спринта

1. Создать `app/webapp/js/modules/ui.js`:
   ```javascript
   // Экспорт класса UI с методами:
   // - showError(message)
   // - hideError()
   // - showLoading(text)
   // - hideLoading()
   // - showResult()
   // - hideResult()
   // - showShareButton()
   // - hideShareButton()
   // - scrollToResult()
   // - disableForm()
   // - enableForm()
   ```

2. Добавить управление состоянием:
   - Внутреннее состояние `_state` (idle, loading, error, success)
   - Метод `getState()` для отладки
   - Переходы между состояниями (state machine)

3. Добавить анимации:
   - Плавное появление/скрытие элементов (CSS transitions)
   - Scroll с анимацией к результату
   - Telegram Haptic Feedback на действия

4. Добавить accessibility:
   - ARIA атрибуты для loading/error состояний
   - Focus management (при ошибке фокус на первое невалидное поле)

5. Обновить `app/webapp/index.html`:
   - Импортировать `UI`
   - Заменить все вызовы `showError()` на `ui.showError()`
   - Убрать дублирование функций

### Критерии достижения цели
- ✅ Класс `UI` управляет всеми видимыми состояниями
- ✅ Нет прямых вызовов `show()`/`hide()` в main скрипте
- ✅ Анимации работают плавно
- ✅ Haptic feedback срабатывает в Telegram
- ✅ Accessibility проверен через screen reader (опционально)

### Обновление документации
После завершения обнови:
- `docs/rpg.yaml` - добавить компонент `UI` с описанием методов
- `docs/webapp_refactoring_checklist.md` - отметить Этап 6
- `CHANGELOG_georgia.md` - запись о создании UI модуля

---

## СПРИНТ 7: Рендеринг результатов расчёта

**Длительность**: 3-4 часа  
**Сложность**: Средняя  
**Зависимости**: Спринты 2, 3

### Роль модели
Ты — специалист по рендерингу данных, создающий модуль для отображения результатов расчёта с breakdown, meta-информацией и warnings в структурированном виде.

### Источники правды
- `app/webapp/index.html` (строки 1200-1500) - функция `displayResult(result)`
- `app/calculation/models.py` - классы `CalculationResult`, `CostBreakdown`, `CalculationMeta`
- `docs/webapp_refactoring_plan.md` - Этап 7
- `app/api/routes.py` (эндпоинт `/api/meta`) - структура countries для лейблов

### Задачи спринта

1. Создать `app/webapp/js/modules/results.js`:
   ```javascript
   // Экспорт класса ResultsRenderer с методами:
   // - render(result) → отобразить весь результат
   // - renderTotal(breakdown)
   // - renderBreakdown(breakdown)
   // - renderMeta(meta, request)
   // - createBreakdownItem(label, amount, isTotal)
   // - getCountryLabel(code) → emoji + label
   // - getAgeCategory(category) → человекочитаемая метка
   // - addDutyInfo(parts, meta)
   // - addWarnings(parts, meta)
   ```

2. Реализовать рендеринг breakdown:
   - Показывать только ненулевые статьи расхода
   - Форматировать суммы через `formatNumber()` из utils
   - Подсветка итоговой суммы (total)

3. Реализовать рендеринг meta:
   - Страна с эмодзи и лейблом (из `/api/meta` countries)
   - Возраст авто и категория (lt3/3_5/gt5)
   - Объём двигателя или volume_band
   - Детали пошлины (customs_value_eur, duty_rate, duty_percent)

4. Реализовать рендеринг warnings:
   - Иконки для разных типов warnings (⚠️, ℹ️)
   - Цветовое кодирование (красный для ошибок, оранжевый для предупреждений)
   - Warnings из `meta.warnings[]`

5. Обновить `app/webapp/index.html`:
   - Импортировать `ResultsRenderer`
   - Передать metaData (из `/api/meta`) в конструктор
   - Заменить `displayResult()` на `renderer.render(result)`

### Критерии достижения цели
- ✅ Результаты отображаются в том же формате что и раньше
- ✅ Все breakdown статьи показываются корректно
- ✅ Meta-информация полная (страна, возраст, объём, пошлина)
- ✅ Warnings отображаются с правильными цветами
- ✅ Код рендеринга изолирован в одном модуле

### Обновление документации
После завершения обнови:
- `docs/rpg.yaml` - добавить компонент `ResultsRenderer`
- `docs/webapp_refactoring_checklist.md` - отметить Этап 7
- `CHANGELOG_georgia.md` - запись о создании рендерера

---

## СПРИНТ 8: Telegram WebApp хелпер

**Длительность**: 2-3 часа  
**Сложность**: Средняя  
**Зависимости**: Спринт 3

### Роль модели
Ты — интеграционный специалист Telegram, создающий обёртку над Telegram WebApp API для упрощения работы с кнопками, темами и haptic feedback.

### Источники правды
- `app/webapp/index.html` (строки 200-400) - работа с `window.Telegram.WebApp`
- Telegram WebApp Documentation: https://core.telegram.org/bots/webapps
- `docs/webapp_refactoring_plan.md` - упоминания Telegram интеграции
- `app/bot/keyboards.py` - WebApp button в боте

### Задачи спринта

1. Создать `app/webapp/js/modules/telegram.js`:
   ```javascript
   // Экспорт класса TelegramWebAppHelper с методами:
   // - isInTelegram() → bool
   // - ready() → инициализация
   // - expand() → развернуть на весь экран
   // - close() → закрыть WebApp
   // 
   // Main Button:
   // - showMainButton(text)
   // - hideMainButton()
   // - setMainButtonLoading(bool)
   // - onMainButtonClick(callback)
   // 
   // Back Button:
   // - showBackButton()
   // - hideBackButton()
   // - onBackButtonClick(callback)
   // 
   // Theme:
   // - getThemeParams() → цвета темы
   // - isDarkTheme() → bool
   // - onThemeChanged(callback)
   // 
   // Feedback:
   // - hapticFeedback(type) → light/medium/heavy/error/success
   // 
   // Data:
   // - sendData(data) → отправить данные боту
   ```

2. Реализовать fallback для браузера:
   - Если не в Telegram, методы не падают (no-op)
   - `isInTelegram()` возвращает false
   - Main/Back button не показываются

3. Добавить обработку ошибок:
   - Проверка доступности `window.Telegram.WebApp`
   - Graceful degradation при отсутствии API

4. Обновить `app/webapp/index.html`:
   - Импортировать `TelegramWebAppHelper`
   - Заменить прямые вызовы `window.Telegram.WebApp` на методы хелпера
   - Добавить haptic feedback на действия

### Критерии достижения цели
- ✅ WebApp работает в Telegram (проверить через @BotFather)
- ✅ Main Button показывается и работает
- ✅ Back Button возвращает к форме
- ✅ Haptic feedback срабатывает на действия
- ✅ WebApp работает в обычном браузере (без ошибок)

### Обновление документации
После завершения обнови:
- `docs/rpg.yaml` - добавить компонент `TelegramWebAppHelper`
- `docs/webapp_refactoring_checklist.md` - отметить интеграцию с Telegram
- `CHANGELOG_georgia.md` - запись о Telegram хелпере

---

## СПРИНТ 9: Главный контроллер калькулятора

**Длительность**: 3-4 часа  
**Сложность**: Высокая  
**Зависимости**: Спринты 4, 5, 6, 7, 8

### Роль модели
Ты — архитектор приложения, создающий главный контроллер который оркестрирует все модули (API, Validator, UI, Results, Telegram) в единый workflow расчёта стоимости.

### Источники правды
- `app/webapp/index.html` (строки 1400-1548) - функция `calculateCost()` и обработка событий
- `docs/webapp_refactoring_plan.md` - Этап 8
- Все созданные модули из спринтов 4-8
- `docs/webapp_dependency_graph.md` - граф зависимостей

### Задачи спринта

1. Создать `app/webapp/js/modules/calculator.js`:
   ```javascript
   // Экспорт класса CalculatorController с методами:
   // - constructor(telegram, metaData)
   // - setCountry(country)
   // - setFreightType(freightType)
   // - async handleSubmit(form)
   // - buildRequest(formData) → CalculationRequest
   // - updateTelegramButton()
   // - reset()
   ```

2. Реализовать dependency injection:
   - Принимать все модули через конструктор или создавать внутри
   - `this.api = new APIClient()`
   - `this.validator = new FormValidator()`
   - `this.ui = new UI()`
   - `this.resultsRenderer = new ResultsRenderer(metaData)`
   - `this.telegram = telegram`

3. Реализовать workflow расчёта:
   ```
   handleSubmit():
     1. Проверить выбор страны
     2. Валидировать форму (validator)
     3. Показать loading (ui)
     4. Отправить запрос (api)
     5. Отобразить результат (resultsRenderer)
     6. Обновить Telegram кнопки (telegram)
     7. Обработать ошибки (ui + haptic)
   ```

4. Добавить управление состоянием:
   - `selectedCountry`
   - `selectedFreightType`
   - `lastResult`
   - Методы для изменения состояния

5. Обновить `app/webapp/index.html`:
   - Импортировать `CalculatorController`
   - Создать экземпляр в `init()`
   - Подключить события формы к `calculator.handleSubmit()`
   - Убрать весь код расчёта из HTML

### Критерии достижения цели
- ✅ Весь flow расчёта проходит через `CalculatorController`
- ✅ В `index.html` нет бизнес-логики (только события)
- ✅ Расчёт работает как раньше (проверить все страны)
- ✅ Обработка ошибок работает корректно
- ✅ Telegram интеграция работает (Main Button, Back Button)

### Обновление документации
После завершения обнови:
- `docs/rpg.yaml` - добавить компонент `CalculatorController` с зависимостями
- `docs/webapp_refactoring_checklist.md` - отметить Этап 8
- `docs/webapp_dependency_graph.md` - обновить граф (контроллер в центре)
- `CHANGELOG_georgia.md` - запись о создании контроллера

---

## СПРИНТ 10: Финализация - минимизация index.html

**Длительность**: 2-3 часа  
**Сложность**: Средняя  
**Зависимости**: Спринт 9

### Роль модели
Ты — рефакторинг-специалист, завершающий миграцию на модульную структуру путём минимизации index.html до чистого HTML/CSS с минимальным bootstrap скриптом.

### Источники правды
- `app/webapp/index.html` - текущее состояние (должно быть ~800 строк после спринтов 1-9)
- `docs/webapp_refactoring_plan.md` - Этап 9
- `app/webapp/index.html.backup` - оригинальное состояние для сравнения

### Задачи спринта

1. Очистить `app/webapp/index.html`:
   - Убрать все `<script>` блоки кроме bootstrap
   - Оставить только структурный HTML
   - Секция `<head>` с мета-тегами и CSS links
   - Секция `<body>` с формой и результатами

2. Создать bootstrap скрипт:
   ```javascript
   <script type="module">
     import { CalculatorController } from './js/modules/calculator.js';
     import { TelegramWebAppHelper } from './js/modules/telegram.js';
     import { APIClient } from './js/modules/api.js';
     
     let calculator;
     
     async function init() {
       // 1. Telegram
       const telegram = new TelegramWebAppHelper();
       telegram.ready();
       telegram.expand();
       
       // 2. Load meta
       const api = new APIClient();
       const metaData = await api.getMeta();
       
       // 3. Controller
       calculator = new CalculatorController(telegram, metaData);
       
       // 4. Events
       setupEventListeners();
       
       // 5. Populate countries
       populateCountries(metaData.countries);
     }
     
     function setupEventListeners() { /* ... */ }
     function populateCountries(countries) { /* ... */ }
     
     init().catch(console.error);
   </script>
   ```

3. Создать вспомогательные функции в отдельном файле:
   - `app/webapp/js/modules/init.js` с `setupEventListeners()` и `populateCountries()`
   - Импортировать в bootstrap скрипт

4. Финальная проверка:
   - Удалить закомментированный код
   - Проверить что нет дублирования
   - Проверить что все функции импортируются

5. Сравнить с бэкапом:
   - Функциональность та же
   - Количество строк: было 1548 → стало ~200 в HTML + модули
   - Запустить все тестовые сценарии

### Критерии достижения цели
- ✅ `index.html` содержит только структуру (~150-200 строк)
- ✅ Весь JavaScript в модулях (app/webapp/js/)
- ✅ Весь CSS в файлах (app/webapp/css/)
- ✅ WebApp работает идентично оригиналу
- ✅ Все страны, расчёты, валидации работают
- ✅ Telegram интеграция работает
- ✅ Тесты из `tests/functional/test_api.py` проходят

### Обновление документации
После завершения обнови:
- `docs/webapp_refactoring_summary.md` - отметить завершение
- `docs/webapp_refactoring_checklist.md` - отметить все этапы выполненными
- `docs/rpg.yaml` - обновить описание app_webapp с новой структурой
- `CHANGELOG_georgia.md` - итоговая запись о завершении рефакторинга
- Создать `docs/webapp_architecture.md` - описание финальной архитектуры

---

## СПРИНТ 11 (ОПЦИОНАЛЬНЫЙ): Базовые unit-тесты

**Длительность**: 2-3 часа  
**Сложность**: Низкая  
**Зависимости**: Спринт 10

### Роль модели
Ты — QA инженер, создающий простые unit-тесты для утилит и модулей без использования сложных фреймворков (только нативный JS в браузере).

### Источники правды
- `docs/webapp_refactoring_plan.md` - Этап 10
- Все созданные модули из спринтов 2-9
- `tests/functional/test_api.py` - примеры тестов на бэкенде

### Задачи спринта

1. Создать `tests/manual/test_utils.html`:
   - Тесты для `formatters.js`
   - Тесты для `dom.js` (debounce, throttle)

2. Создать `tests/manual/test_validator.html`:
   - Тесты для `FormValidator`
   - Валидные и невалидные данные

3. Создать `tests/manual/test_api.html`:
   - Mock API responses
   - Тесты retry логики
   - Тесты timeout

4. Создать `tests/manual/test_renderer.html`:
   - Тесты рендеринга breakdown
   - Тесты рендеринга meta
   - Тесты warnings

5. Создать `tests/manual/README.md`:
   - Инструкция как запустить тесты
   - Список всех тестов
   - Ожидаемые результаты

### Критерии достижения цели
- ✅ Все тесты проходят при открытии в браузере
- ✅ Тесты покрывают основные утилиты (formatters, validator)
- ✅ Тесты легко запустить (просто открыть HTML)
- ✅ Нет зависимости от внешних библиотек

### Обновление документации
После завершения обнови:
- `docs/rpg.yaml` - обновить test coverage для webapp компонентов
- `docs/webapp_refactoring_checklist.md` - отметить тестирование
- `CHANGELOG_georgia.md` - запись о добавлении тестов

---

## Шаблон промпта для выполнения спринта

Для каждого спринта используй следующий промпт:

```
Выполни СПРИНТ {N}: {Название}

**Контекст проекта:**
- Проект: car_calculator (FastAPI + Telegram Bot + WebApp)
- Текущая задача: Рефакторинг webapp/index.html (1548 строк) на модульную структуру
- Методика: RPG (Repository Planning Graph)
- Принцип: Избегаем оверинжиниринга, используем vanilla JS + ES6 модули

**Источники правды (Sources of Truth):**
1. `docs/webapp_refactoring_plan.md` - детальный план (Этап {N})
2. `docs/rpg.yaml` - граф проекта
3. [Дополнительные файлы из секции "Источники правды" спринта]

**Роль:**
{Роль из описания спринта}

**Задачи на спринт:**
{Список задач из описания спринта}

**Критерии достижения цели:**
{Чеклист из описания спринта}

**Важно:**
- После создания файлов проверь их на ошибки
- Убедись что WebApp продолжает работать
- Проверь в браузере (локально) и в Telegram WebApp
- Соблюдай стиль кода (ES6, чистые функции, JSDoc комментарии)

**После завершения:**
Обнови документацию согласно секции "Обновление документации"
```

---

## Порядок выполнения спринтов

```mermaid
graph TD
    S0[Sprint 0: Подготовка] --> S1[Sprint 1: CSS]
    S1 --> S2[Sprint 2: Utils]
    S1 --> S3[Sprint 3: Config]
    S2 --> S4[Sprint 4: Validator]
    S2 --> S6[Sprint 6: UI]
    S3 --> S4
    S3 --> S5[Sprint 5: API Client]
    S3 --> S6
    S2 --> S7[Sprint 7: Results]
    S3 --> S7
    S3 --> S8[Sprint 8: Telegram]
    S4 --> S9[Sprint 9: Controller]
    S5 --> S9
    S6 --> S9
    S7 --> S9
    S8 --> S9
    S9 --> S10[Sprint 10: Finalize]
    S10 --> S11[Sprint 11: Tests (opt)]
```

**Параллельные спринты** (можно выполнять одновременно):
- Спринты 2 и 3 (Utils и Config независимы)
- Спринты 5 и 6 (API Client и UI независимы)
- Спринты 7 и 8 (Results и Telegram независимы)

**Критический путь**:
S0 → S1 → S2 → S4 → S9 → S10 (минимум 13-19 часов)

---

## Метрики успеха всего рефакторинга

### Технические
- ✅ Количество файлов > 200 строк: 0
- ✅ Количество модулей: ~10
- ✅ Дублирование кода: 0%
- ✅ Тестовое покрытие утилит: >80%

### Качественные
- ✅ Время добавления новой страны: с 4ч до 30 мин
- ✅ Время изменения текста кнопки: 1 файл (вместо поиска по HTML)
- ✅ Время onboarding нового разработчика: с 4ч до 30 мин
- ✅ Количество багов после рефакторинга: 0 (полная обратная совместимость)

### Производительность
- ✅ Размер JS (gzip): уменьшение на 20-30%
- ✅ Браузерное кэширование: CSS/JS кэшируются
- ✅ Time to Interactive: без изменений или быстрее
- ✅ Lighthouse Score: ≥90

---

## Заключение

Этот план разбивает большой рефакторинг на 11 управляемых спринтов. Каждый спринт:
- Имеет чёткую роль и задачи
- Указывает источники правды
- Даёт критерии завершения
- Требует обновления документации

Следуя методике RPG:
- **Явная структура**: спринты следуют графу зависимостей
- **Топологический порядок**: от utils к controller
- **Инкрементальная проверка**: после каждого спринта всё работает
- **Избегаем оверинжиниринга**: простые решения, без TypeScript/фреймворков

Общее время: **22-35 часов** (3-5 рабочих дней)

