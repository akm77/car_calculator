# План рефакторинга WebApp (без оверинжиниринга)

**Цель**: Улучшить структуру, поддерживаемость и расширяемость webapp, сохраняя простоту

**Принципы**:
- ✅ Постепенный рефакторинг (работает на каждом шаге)
- ✅ Практичность (реальная польза, не теория)
- ✅ KISS (Keep It Simple, Stupid)
- ❌ Без оверинжиниринга (TypeScript, сложные фреймворки, микрофронтенды)
- ❌ Без излишних инструментов (E2E тесты, Sentry, аналитика пока не нужны)

---

## Этап 0: Подготовка (1-2 часа)

### 0.1. Создать структуру папок
```bash
mkdir -p app/webapp/js/{modules,utils,config}
mkdir -p app/webapp/css
```

### 0.2. Зафиксировать текущее состояние
```bash
# Создать бэкап текущего работающего index.html
cp app/webapp/index.html app/webapp/index.html.backup

# Создать тестовый файл для проверки после каждого изменения
# tests/manual/test_webapp_manually.md
```

**Критерий готовности**: Структура папок создана, бэкап есть

---

## Этап 1: Вынос CSS (2-3 часа)

### 1.1. Извлечь CSS из HTML
**Файлы для создания**:
- `app/webapp/css/variables.css` - CSS переменные
- `app/webapp/css/base.css` - Базовые стили (body, container, reset)
- `app/webapp/css/components.css` - Компоненты (buttons, cards, forms)
- `app/webapp/css/telegram.css` - Telegram-специфичные стили

**Действие**:
```html
<!-- В index.html заменить <style>...</style> на: -->
<link rel="stylesheet" href="/static/css/variables.css">
<link rel="stylesheet" href="/static/css/base.css">
<link rel="stylesheet" href="/static/css/components.css">
<link rel="stylesheet" href="/static/css/telegram.css">
```

**Проверка**: Открыть webapp, убедиться что стили работают

**Польза**: 
- CSS можно редактировать отдельно
- Браузер кэширует CSS файлы
- Проще искать нужные стили

---

## Этап 2: Вынос утилит (3-4 часа)

### 2.1. Создать модуль форматирования
**Файл**: `app/webapp/js/utils/formatters.js`

```javascript
// Чистые функции без зависимостей
export function formatNumber(num) {
    if (num == null || isNaN(num)) return '—';
    return new Intl.NumberFormat('ru-RU', { 
        maximumFractionDigits: 0 
    }).format(num);
}

export function formatCurrency(amount, currency) {
    if (amount == null || isNaN(amount)) return '—';
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: currency || 'RUB',
        maximumFractionDigits: 0
    }).format(amount);
}

export function getAgeCategory(category) {
    const labels = {
        'lt3': 'до 3 лет',
        '3_5': '3-5 лет',
        'gt5': 'более 5 лет'
    };
    return labels[category] || category;
}
```

### 2.2. Создать модуль DOM утилит
**Файл**: `app/webapp/js/utils/dom.js`

```javascript
// Простые DOM helpers
export function show(element) {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    if (element) element.classList.add('show');
}

export function hide(element) {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    if (element) element.classList.remove('show');
}

export function setContent(elementId, html) {
    const el = document.getElementById(elementId);
    if (el) el.innerHTML = html;
}

export function setText(elementId, text) {
    const el = document.getElementById(elementId);
    if (el) el.textContent = text;
}

// Debounce для оптимизации
export function debounce(fn, delay = 300) {
    let timer;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}
```

**Проверка**: Импортировать в index.html, заменить вызовы функций

**Польза**:
- Переиспользуемые функции
- Легко тестировать (просто импортируй и вызови)
- Меньше дублирования

---

## Этап 3: Вынос констант и конфигурации (1-2 часа)

### 3.1. Создать файл сообщений
**Файл**: `app/webapp/js/config/messages.js`

```javascript
export const Messages = {
    errors: {
        NO_COUNTRY: 'Пожалуйста, выберите страну покупки',
        INVALID_YEAR_FUTURE: 'Год выпуска не может быть больше текущего',
        INVALID_YEAR_OLD: 'Год выпуска должен быть не менее 1990',
        INVALID_ENGINE: 'Объем двигателя должен быть от 500 до 10000 см³',
        INVALID_PRICE: 'Цена покупки должна быть больше 0',
        CALCULATION_ERROR: 'Ошибка расчета',
        NETWORK_ERROR: 'Ошибка сети. Проверьте подключение.'
    },
    
    buttons: {
        CALCULATE: 'Рассчитать стоимость',
        BACK: '↩️ Вернуться к расчётам',
        SHARE: '📤 Поделиться',
        LOADING: 'Производится расчёт...'
    },
    
    labels: {
        TOTAL: 'ИТОГО',
        COUNTRY: 'Страна покупки',
        AGE: 'Возраст авто',
        ENGINE: 'Объем двигателя',
        CUSTOMS_VALUE: 'Таможенная стоимость',
        DUTY_RATE: 'Ставка пошлины'
    }
};
```

### 3.2. Создать файл констант
**Файл**: `app/webapp/js/config/constants.js`

```javascript
export const Constraints = {
    YEAR_MIN: 1990,
    YEAR_MAX: () => new Date().getFullYear(),
    ENGINE_CC_MIN: 500,
    ENGINE_CC_MAX: 10000,
    PRICE_MIN: 1
};

export const API_ENDPOINTS = {
    CALCULATE: '/api/calculate',
    META: '/api/meta',
    RATES: '/api/rates',
    HEALTH: '/api/health'
};

export const API_CONFIG = {
    RETRY_COUNT: 3,
    RETRY_DELAY: 1000,
    TIMEOUT: 30000
};

export const DEFAULT_VALUES = {
    FREIGHT_TYPE: 'open',
    VEHICLE_TYPE: 'M1',
    CURRENCY: 'JPY'
};
```

**Проверка**: Заменить хардкод значения на импорты из констант

**Польза**:
- Одно место для изменения текстов/значений
- Легко локализовать (добавить en.js, de.js)
- Нет магических чисел в коде

---

## Этап 4: Извлечь валидацию (2-3 часа)

### 4.1. Создать модуль валидации
**Файл**: `app/webapp/js/modules/validator.js`

```javascript
import { Constraints } from '../config/constants.js';
import { Messages } from '../config/messages.js';

export class FormValidator {
    constructor(constraints = Constraints) {
        this.constraints = constraints;
    }
    
    validate(formData) {
        const errors = [];
        
        // Валидация года
        const year = parseInt(formData.get('year'));
        const maxYear = typeof this.constraints.YEAR_MAX === 'function' 
            ? this.constraints.YEAR_MAX() 
            : this.constraints.YEAR_MAX;
            
        if (year > maxYear) {
            errors.push(Messages.errors.INVALID_YEAR_FUTURE);
        }
        if (year < this.constraints.YEAR_MIN) {
            errors.push(Messages.errors.INVALID_YEAR_OLD);
        }
        
        // Валидация объема
        const engineCc = parseInt(formData.get('engineCc'));
        if (engineCc < this.constraints.ENGINE_CC_MIN || 
            engineCc > this.constraints.ENGINE_CC_MAX) {
            errors.push(Messages.errors.INVALID_ENGINE);
        }
        
        // Валидация цены
        const price = parseFloat(formData.get('purchasePrice'));
        if (price <= 0) {
            errors.push(Messages.errors.INVALID_PRICE);
        }
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }
    
    validateField(name, value) {
        // Для валидации отдельных полей в реальном времени
        switch(name) {
            case 'year':
                const year = parseInt(value);
                const maxYear = typeof this.constraints.YEAR_MAX === 'function' 
                    ? this.constraints.YEAR_MAX() 
                    : this.constraints.YEAR_MAX;
                if (year > maxYear) return Messages.errors.INVALID_YEAR_FUTURE;
                if (year < this.constraints.YEAR_MIN) return Messages.errors.INVALID_YEAR_OLD;
                break;
            case 'engineCc':
                const cc = parseInt(value);
                if (cc < this.constraints.ENGINE_CC_MIN || 
                    cc > this.constraints.ENGINE_CC_MAX) {
                    return Messages.errors.INVALID_ENGINE;
                }
                break;
            case 'purchasePrice':
                if (parseFloat(value) <= 0) return Messages.errors.INVALID_PRICE;
                break;
        }
        return null; // Нет ошибок
    }
}
```

**Проверка**: Заменить функцию `validateForm()` на использование `FormValidator`

**Польза**:
- Валидация в одном месте
- Легко добавить новые правила
- Можно валидировать поля по отдельности

---

## Этап 5: Извлечь API клиент (2-3 часа)

### 5.1. Улучшить класс APIClient
**Файл**: `app/webapp/js/modules/api.js`

```javascript
import { API_ENDPOINTS, API_CONFIG } from '../config/constants.js';
import { Messages } from '../config/messages.js';

export class APIError extends Error {
    constructor(message, status, details = null) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.details = details;
    }
}

export class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.retryCount = API_CONFIG.RETRY_COUNT;
        this.retryDelay = API_CONFIG.RETRY_DELAY;
        this.timeout = API_CONFIG.TIMEOUT;
    }

    async fetchWithTimeout(url, options = {}) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new APIError('Превышено время ожидания', 408);
            }
            throw error;
        }
    }

    async fetchWithRetry(url, options = {}, attempt = 1) {
        try {
            const response = await this.fetchWithTimeout(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new APIError(
                    error.detail || `HTTP ${response.status}`,
                    response.status,
                    error
                );
            }

            return response;
        } catch (error) {
            // Retry только на сетевых ошибках, не на 4xx/5xx
            if (error instanceof APIError || attempt >= this.retryCount) {
                throw error;
            }

            console.warn(`API retry ${attempt}/${this.retryCount}:`, error.message);
            await new Promise(resolve => 
                setTimeout(resolve, this.retryDelay * attempt)
            );
            return this.fetchWithRetry(url, options, attempt + 1);
        }
    }

    getURL(path) {
        return this.baseURL + path;
    }

    async get(path) {
        const response = await this.fetchWithRetry(this.getURL(path));
        return response.json();
    }

    async post(path, data) {
        const response = await this.fetchWithRetry(this.getURL(path), {
            method: 'POST',
            body: JSON.stringify(data)
        });
        return response.json();
    }

    // Специфичные методы для нашего API
    async calculate(request) {
        try {
            return await this.post(API_ENDPOINTS.CALCULATE, request);
        } catch (error) {
            if (error instanceof APIError) {
                throw error;
            }
            throw new APIError(Messages.errors.NETWORK_ERROR, 0);
        }
    }

    async getMeta() {
        return await this.get(API_ENDPOINTS.META);
    }

    async getRates() {
        return await this.get(API_ENDPOINTS.RATES);
    }
}
```

**Проверка**: Заменить использование `api.post()` на `api.calculate()`

**Польза**:
- Централизованная обработка ошибок
- Таймауты защищают от зависания
- Retry логика для ненадежных соединений
- Типизированные ошибки (APIError)

---

## Этап 6: Создать модуль UI (3-4 часа)

### 6.1. Извлечь UI логику
**Файл**: `app/webapp/js/modules/ui.js`

```javascript
import { show, hide, setText, setContent } from '../utils/dom.js';
import { Messages } from '../config/messages.js';

export class UI {
    constructor() {
        this.errorElement = document.getElementById('error');
        this.loadingElement = document.getElementById('loading');
        this.resultElement = document.getElementById('resultCard');
    }

    showError(message) {
        setText('errorMessage', message);
        show(this.errorElement);
    }

    hideError() {
        hide(this.errorElement);
    }

    showLoading(text = Messages.buttons.LOADING) {
        setText('loadingText', text);
        show(this.loadingElement);
    }

    hideLoading() {
        hide(this.loadingElement);
    }

    showResult() {
        show(this.resultElement);
        // Scroll to result
        this.resultElement.scrollIntoView({ behavior: 'smooth' });
    }

    hideResult() {
        hide(this.resultElement);
    }

    showShareButton() {
        const btn = document.getElementById('shareBtn');
        if (btn) btn.style.display = 'block';
    }

    hideShareButton() {
        const btn = document.getElementById('shareBtn');
        if (btn) btn.style.display = 'none';
    }
}
```

**Проверка**: Заменить вызовы `showError()`, `showLoading()` на `ui.showError()`, etc.

**Польза**:
- Единое место управления UI
- Легко добавить анимации/улучшения
- Проще менять структуру DOM

---

## Этап 7: Создать модуль рендеринга результатов (3-4 часа)

### 7.1. Извлечь логику отображения результатов
**Файл**: `app/webapp/js/modules/results.js`

```javascript
import { formatNumber } from '../utils/formatters.js';
import { setText, setContent } from '../utils/dom.js';
import { Messages } from '../config/messages.js';

export class ResultsRenderer {
    constructor(metaData = null) {
        this.metaData = metaData;
    }

    render(result) {
        this.renderTotal(result.breakdown);
        this.renderBreakdown(result.breakdown);
        this.renderMeta(result.meta, result.request);
    }

    renderTotal(breakdown) {
        const formatted = formatNumber(breakdown.total_rub) + ' ₽';
        setText('totalAmount', formatted);
    }

    renderBreakdown(breakdown) {
        const items = [
            { label: 'Закупочная стоимость', amount: breakdown.purchase_price_rub },
            { label: 'Расходы в стране', amount: breakdown.country_expenses_rub },
            { label: 'Фрахт', amount: breakdown.freight_rub },
            { label: 'Таможенная пошлина', amount: breakdown.duties_rub },
            { label: 'Таможенное оформление', amount: breakdown.customs_services_rub },
            { label: 'Утилизационный сбор', amount: breakdown.utilization_fee_rub },
            { label: 'Эра-Глонасс', amount: breakdown.era_glonass_rub },
            { label: 'Вознаграждение компании', amount: breakdown.company_commission_rub }
        ];

        const html = items
            .filter(item => item.amount > 0)
            .map(item => this.createBreakdownItem(item.label, item.amount))
            .join('');

        const totalHtml = this.createBreakdownItem(
            Messages.labels.TOTAL, 
            breakdown.total_rub, 
            true
        );

        setContent('breakdown', html + totalHtml);
    }

    createBreakdownItem(label, amount, isTotal = false) {
        const className = isTotal ? 'breakdown-item total' : 'breakdown-item';
        return `
            <div class="${className}">
                <span class="breakdown-label">${label}</span>
                <span class="breakdown-amount">${formatNumber(amount)} ₽</span>
            </div>
        `;
    }

    renderMeta(meta, request) {
        const parts = [];

        // Country
        const countryLabel = this.getCountryLabel(request.country);
        if (countryLabel) {
            parts.push(`<div>${Messages.labels.COUNTRY}: ${countryLabel}</div>`);
        }

        // Age
        parts.push(`<div>${Messages.labels.AGE}: ${meta.age_years} лет (${this.getAgeCategory(meta.age_category)})</div>`);

        // Engine
        const engineDisplay = this.getEngineDisplay(meta, request);
        parts.push(`<div>${Messages.labels.ENGINE}: ${engineDisplay}</div>`);

        // Duty details
        this.addDutyInfo(parts, meta);

        // Warnings
        this.addWarnings(parts, meta);

        setContent('metaInfo', parts.join(''));
    }

    getEngineDisplay(meta, request) {
        if (meta && meta.volume_band && 
            meta.volume_band !== 'value_brackets' && 
            meta.volume_band !== 'n/a') {
            return meta.volume_band;
        }
        return request?.engine_cc ? `${request.engine_cc} см³` : '—';
    }

    addDutyInfo(parts, meta) {
        if (meta.customs_value_eur != null) {
            parts.push(`<div>${Messages.labels.CUSTOMS_VALUE}: ${formatNumber(Math.round(meta.customs_value_eur))} €</div>`);
        }

        if (meta.duty_formula_mode === 'percent') {
            if (meta.duty_percent != null) {
                parts.push(`<div>Пошлина: ${Math.round(meta.duty_percent * 100)}% от стоимости (минимум по €/см³)</div>`);
            }
            if (meta.duty_min_rate_eur_per_cc != null) {
                parts.push(`<div>Мин. ставка: ${meta.duty_min_rate_eur_per_cc} €/см³</div>`);
            }
            if (meta.duty_value_bracket_max_eur != null) {
                parts.push(`<div>Диапазон до: ${formatNumber(meta.duty_value_bracket_max_eur)} €</div>`);
            }
        } else if (meta.duty_formula_mode === 'per_cc' && meta.duty_rate_eur_per_cc != null) {
            parts.push(`<div>${Messages.labels.DUTY_RATE}: ${meta.duty_rate_eur_per_cc} €/см³</div>`);
        }
    }

    addWarnings(parts, meta) {
        if (meta.vehicle_type && meta.vehicle_type !== 'M1') {
            parts.push('<div style="color:#e67e22;margin-top:8px;">Расчет выполнен с допущениями для не-M1. Уточните условия у поддержки.</div>');
        }

        if (meta.warnings && meta.warnings.length) {
            const warningsHtml = meta.warnings
                .map(w => '⚠️ ' + w.message)
                .join('<br>');
            parts.push(`<div style="color:#e74c3c;margin-top:8px;">${warningsHtml}</div>`);
        }
    }

    getCountryLabel(code) {
        if (this.metaData && Array.isArray(this.metaData.countries)) {
            const country = this.metaData.countries.find(c => c.code === code);
            if (country) {
                return country.emoji ? `${country.emoji} ${country.label}` : country.label;
            }
        }

        // Fallback
        const fallback = {
            japan: '🇯🇵 Япония',
            korea: '🇰🇷 Корея',
            uae: '🇦🇪 ОАЭ',
            china: '🇨🇳 Китай',
            georgia: '🇬🇪 Грузия'
        };
        return fallback[code] || code;
    }

    getAgeCategory(category) {
        const labels = {
            'lt3': 'до 3 лет',
            '3_5': '3-5 лет',
            'gt5': 'более 5 лет'
        };
        return labels[category] || category;
    }
}
```

**Проверка**: Заменить `displayResult()` на использование `ResultsRenderer`

**Польза**:
- Рендеринг в одном месте
- Легко менять формат отображения
- Можно добавить разные форматы (JSON, PDF экспорт)

---

## Этап 8: Создать главный контроллер (3-4 часа)

### 8.1. Объединить всё в контроллере
**Файл**: `app/webapp/js/modules/calculator.js`

```javascript
import { APIClient } from './api.js';
import { FormValidator } from './validator.js';
import { UI } from './ui.js';
import { ResultsRenderer } from './results.js';
import { Messages } from '../config/messages.js';

export class CalculatorController {
    constructor(telegram, metaData) {
        this.api = new APIClient();
        this.validator = new FormValidator();
        this.ui = new UI();
        this.resultsRenderer = new ResultsRenderer(metaData);
        this.telegram = telegram;
        
        this.selectedCountry = null;
        this.selectedFreightType = 'open';
    }

    setCountry(country) {
        this.selectedCountry = country;
    }

    setFreightType(freightType) {
        this.selectedFreightType = freightType;
    }

    async handleSubmit(form) {
        // Проверка страны
        if (!this.selectedCountry) {
            this.ui.showError(Messages.errors.NO_COUNTRY);
            return;
        }

        // Валидация формы
        const formData = new FormData(form);
        const validation = this.validator.validate(formData);
        
        if (!validation.isValid) {
            this.ui.showError(validation.errors[0]);
            return;
        }

        // Подготовка запроса
        const request = this.buildRequest(formData);

        // UI - показать загрузку
        this.ui.showLoading();
        this.ui.hideError();
        this.ui.hideResult();

        try {
            // Telegram - loading state
            if (this.telegram.isInTelegram()) {
                this.telegram.setMainButtonLoading(true);
            }

            // API запрос
            const result = await this.api.calculate(request);

            // Отобразить результат
            this.resultsRenderer.render(result);
            this.ui.showResult();
            this.ui.showShareButton();

            // Сохранить для шаринга
            window.lastCalculationResult = result;

            // Telegram - success
            if (this.telegram.isInTelegram()) {
                this.telegram.hapticFeedback('medium');
                this.telegram.hideMainButton();
                this.telegram.showBackButton();
            }

        } catch (error) {
            console.error('Calculation error:', error);
            
            const message = error.message || Messages.errors.CALCULATION_ERROR;
            this.ui.showError(message);

            if (this.telegram.isInTelegram()) {
                this.telegram.hapticFeedback('heavy');
            }

        } finally {
            this.ui.hideLoading();
            
            if (this.telegram.isInTelegram()) {
                this.telegram.setMainButtonLoading(false);
            }
        }
    }

    buildRequest(formData) {
        return {
            country: this.selectedCountry,
            year: parseInt(formData.get('year')),
            engine_cc: parseInt(formData.get('engineCc')),
            purchase_price: parseFloat(formData.get('purchasePrice')),
            currency: formData.get('currency'),
            freight_type: this.selectedFreightType,
            vehicle_type: formData.get('vehicleType') || 'M1'
        };
    }

    // Для обновления состояния Telegram кнопки
    updateTelegramButton() {
        if (!this.telegram.isInTelegram()) return;
        
        if (!this.selectedCountry) {
            this.telegram.hideMainButton();
            return;
        }

        const form = document.getElementById('calculatorForm');
        const formData = new FormData(form);
        const hasRequired = formData.get('year') && 
                           formData.get('engineCc') && 
                           formData.get('purchasePrice');

        if (hasRequired) {
            this.telegram.showMainButton(Messages.buttons.CALCULATE);
        } else {
            this.telegram.hideMainButton();
        }
    }
}
```

**Проверка**: Заменить функцию `calculateCost()` на `calculator.handleSubmit()`

**Польза**:
- Единая точка входа для расчёта
- Явные зависимости
- Легко добавить новую функциональность

---

## Этап 9: Обновить index.html (2-3 часа)

### 9.1. Минимизировать HTML
**Файл**: `app/webapp/index.html`

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Калькулятор растаможки авто</title>
    
    <!-- PWA -->
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#2481cc">
    
    <!-- Telegram Web App -->
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    
    <!-- Styles -->
    <link rel="stylesheet" href="/static/css/variables.css">
    <link rel="stylesheet" href="/static/css/base.css">
    <link rel="stylesheet" href="/static/css/components.css">
    <link rel="stylesheet" href="/static/css/telegram.css">
</head>
<body>
    <div class="container">
        <!-- Header, Form, Results (HTML остаётся) -->
    </div>

    <!-- Scripts -->
    <script type="module">
        import { CalculatorController } from './js/modules/calculator.js';
        import { TelegramWebAppHelper } from './js/modules/telegram.js';
        import { debounce } from './js/utils/dom.js';

        // Инициализация
        let telegram;
        let calculator;
        let metaData;

        async function init() {
            // 1. Telegram
            telegram = new TelegramWebAppHelper();

            // 2. Загрузить мета-данные
            try {
                const api = new (await import('./js/modules/api.js')).APIClient();
                metaData = await api.getMeta();
                populateCountries(metaData.countries);
            } catch (error) {
                console.warn('Failed to load meta:', error);
                populateCountries(getFallbackCountries());
            }

            // 3. Создать контроллер
            calculator = new CalculatorController(telegram, metaData);

            // 4. Подключить события
            setupEventListeners();
        }

        function setupEventListeners() {
            // Форма
            const form = document.getElementById('calculatorForm');
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await calculator.handleSubmit(form);
            });

            // Страна
            document.getElementById('countrySelect').addEventListener('change', (e) => {
                calculator.setCountry(e.target.value);
                updateCurrencyAndFreight();
                telegram.hapticFeedback('light');
            });

            // Обновление кнопки (с debounce)
            const debouncedUpdate = debounce(() => calculator.updateTelegramButton(), 300);
            form.addEventListener('input', debouncedUpdate);

            // Share
            document.getElementById('shareBtn').addEventListener('click', shareResult);

            // Другие события...
        }

        // Вспомогательные функции (упрощенные)
        function populateCountries(countries) { /* ... */ }
        function updateCurrencyAndFreight() { /* ... */ }
        function shareResult() { /* ... */ }
        function getFallbackCountries() { /* ... */ }

        // Запуск
        init();
    </script>
</body>
</html>
```

**Проверка**: Полное тестирование всех функций webapp

**Польза**:
- HTML сфокусирован на структуре
- JS логика вынесена в модули
- Легко понять что делает приложение

---

## Этап 10: Добавить базовые тесты (опционально, 2-3 часа)

### 10.1. Простые unit-тесты для утилит
**Файл**: `tests/unit/test_formatters.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>Formatters Tests</title>
</head>
<body>
    <h1>Tests</h1>
    <div id="results"></div>

    <script type="module">
        import { formatNumber, getAgeCategory } from '../../app/webapp/js/utils/formatters.js';

        function test(name, fn) {
            try {
                fn();
                console.log('✅', name);
                document.getElementById('results').innerHTML += `<div>✅ ${name}</div>`;
            } catch (error) {
                console.error('❌', name, error);
                document.getElementById('results').innerHTML += `<div>❌ ${name}: ${error.message}</div>`;
            }
        }

        function assert(condition, message) {
            if (!condition) throw new Error(message);
        }

        // Тесты
        test('formatNumber форматирует число', () => {
            assert(formatNumber(1000) === '1 000', 'Should format 1000');
            assert(formatNumber(1234567) === '1 234 567', 'Should format 1234567');
        });

        test('formatNumber обрабатывает null', () => {
            assert(formatNumber(null) === '—', 'Should return dash for null');
            assert(formatNumber(undefined) === '—', 'Should return dash for undefined');
        });

        test('getAgeCategory возвращает правильные метки', () => {
            assert(getAgeCategory('lt3') === 'до 3 лет', 'lt3 label');
            assert(getAgeCategory('3_5') === '3-5 лет', '3_5 label');
            assert(getAgeCategory('gt5') === 'более 5 лет', 'gt5 label');
        });
    </script>
</body>
</html>
```

**Проверка**: Открыть test_formatters.html в браузере, все тесты должны пройти

**Польза**:
- Быстрая проверка что утилиты работают
- Нет зависимости от тестовых фреймворков
- Запускается прямо в браузере

---

## Чеклист завершения

### После каждого этапа:
- [ ] Код работает в браузере
- [ ] Нет ошибок в консоли
- [ ] Telegram WebApp работает
- [ ] Расчёт возвращает корректный результат
- [ ] Коммит в git с описанием

### После всего рефакторинга:
- [ ] Размер JS уменьшился (gzip)
- [ ] Браузер кэширует CSS/JS файлы
- [ ] Легко найти нужную функцию
- [ ] Легко добавить новую страну
- [ ] Код читается без комментариев
- [ ] Нет дублирования валидации/констант

---

## Оценка времени

| Этап | Описание | Время |
|------|----------|-------|
| 0 | Подготовка | 1-2ч |
| 1 | Вынос CSS | 2-3ч |
| 2 | Утилиты | 3-4ч |
| 3 | Константы | 1-2ч |
| 4 | Валидация | 2-3ч |
| 5 | API клиент | 2-3ч |
| 6 | UI модуль | 3-4ч |
| 7 | Results рендер | 3-4ч |
| 8 | Контроллер | 3-4ч |
| 9 | Обновить HTML | 2-3ч |
| 10 | Базовые тесты | 2-3ч (опц.) |
| **ИТОГО** | | **22-35ч** |

**Реалистичная оценка**: 3-5 рабочих дней (по 6-8 часов)

---

## Критерии успеха

### Технические метрики
- ✅ Каждый файл < 300 строк
- ✅ Нет глобальных переменных (кроме `telegram`, `calculator` в main)
- ✅ Нет дублирования кода
- ✅ Нет магических чисел/строк
- ✅ CSS/JS кэшируются браузером

### Качественные метрики
- ✅ Добавление новой страны: 30 минут (вместо 4 часов)
- ✅ Изменение текста кнопки: 1 файл (вместо поиска по HTML)
- ✅ Добавление новой валидации: 5 строк в validator.js
- ✅ Новый разработчик понимает структуру за 30 минут

---

## Что НЕ делаем (избегаем оверинжиниринга)

❌ **TypeScript** - сложная настройка, компиляция, лишняя сложность  
❌ **React/Vue/Svelte** - избыточно для простого калькулятора  
❌ **Webpack/Vite** - нативные ES модули работают в браузере  
❌ **E2E тесты (Playwright)** - сложная настройка CI/CD  
❌ **Sentry/Error tracking** - пока нет реальных пользователей  
❌ **Google Analytics** - GDPR, настройка, избыточно на старте  
❌ **State Management (Redux)** - простой объект `calculator` достаточно  
❌ **Микрофронтенды** - 1500 строк не требуют такой архитектуры  
❌ **GraphQL** - REST API работает отлично  
❌ **Service Workers кэширование** - PWA manifest уже есть, достаточно  

---

## Итого

Этот план даёт:
- ✅ **Модульность** - можно редактировать части независимо
- ✅ **Читаемость** - легко понять что где находится
- ✅ **Расширяемость** - легко добавить новые фичи
- ✅ **Поддерживаемость** - легко найти и исправить баги
- ✅ **Простота** - нет лишних инструментов и фреймворков

Следуя RPG принципам:
- **Явная структура** через папки modules/utils/config
- **Топологический порядок** от utils к контроллеру
- **Стабильные интерфейсы** через явные импорты/экспорты
- **Инкрементальная проверка** после каждого этапа

