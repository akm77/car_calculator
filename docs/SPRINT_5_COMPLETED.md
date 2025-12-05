# SPRINT 5 COMPLETED: HTTP Client with Retry/Timeout/Error Handling ✅

**Дата завершения**: December 5, 2025  
**Время выполнения**: 2 часа  
**Методология**: RPG - Reliable Network Operations

---

## 📦 Что было создано

### 1. API Client Module (`app/webapp/js/modules/api.js`)
**Размер**: 481 строк  
**Экспорты**: `api` (singleton), `APIClient`, `APIError`

#### APIError Class
Кастомная ошибка с контекстом и типизацией:
```javascript
new APIError(message, status, code, details)
```

**Свойства**:
- `message` - Текст ошибки
- `status` - HTTP статус (или null для сетевых ошибок)
- `code` - Тип ошибки (NetworkError, TimeoutError, ValidationError, ServerError)
- `details` - Дополнительные данные от сервера
- `timestamp` - ISO timestamp создания ошибки

**Методы**:
- `isNetworkError()` - Проверка сетевой ошибки
- `isTimeoutError()` - Проверка timeout
- `isValidationError()` - Проверка 4xx ошибки
- `isServerError()` - Проверка 5xx ошибки
- `getUserMessage()` - Понятное пользователю сообщение
- `toLogFormat()` - Структурированный формат для логов

#### APIClient Class
Robust HTTP клиент с retry и timeout:

**Конфигурация**:
```javascript
new APIClient({
    baseURL: 'auto-detected',  // или custom
    timeout: 10000,             // 10 секунд
    maxRetries: 3,              // 3 попытки
    retryDelay: 1000,           // 1 секунда (exponential)
    csrfToken: 'auto-generated'
})
```

**Core методы**:
- `fetchWithTimeout(url, options, timeout)` - Timeout через AbortController
- `fetchWithRetry(url, options, maxRetries)` - Retry с exponential backoff
- `parseErrorResponse(response)` - Парсинг FastAPI {"detail": "..."}
- `createHTTPError(status, errorData)` - Создание типизированной ошибки

**Generic HTTP методы**:
- `get(path, options)` → Promise<any>
- `post(path, data, options)` → Promise<any>

**Специфичные методы для car_calculator**:
- `calculate(formData)` → Promise<CalculationResult>
- `getMeta()` → Promise<MetaData>
- `getRates()` → Promise<RatesData>
- `refreshRates()` → Promise<RatesData>
- `health()` → Promise<HealthStatus>

---

## 🔧 Retry Logic (Exponential Backoff)

### Когда срабатывает retry?
- ✅ Сетевые ошибки (нет соединения, CORS, DNS failure)
- ✅ Timeout ошибки (AbortError)
- ❌ **НЕ** срабатывает на 4xx (validation errors) - предотвращает дублирование
- ❌ **НЕ** срабатывает на 5xx (server errors) - сервер уже получил запрос

### Exponential backoff
```
Попытка 1: немедленно
Попытка 2: через 1s  (1000 × 2^0)
Попытка 3: через 2s  (1000 × 2^1)
Попытка 4: через 4s  (1000 × 2^2)
```

### Логирование
```javascript
[APIClient] Attempt 1 failed: Network error. Retrying in 1000ms...
[APIClient] Attempt 2 failed: Network error. Retrying in 2000ms...
[APIClient] Request succeeded on attempt 3
```

---

## ⏱️ Timeout Handling

### Реализация через AbortController
```javascript
const controller = new AbortController();
setTimeout(() => controller.abort(), timeout);
fetch(url, { signal: controller.signal });
```

### Обработка timeout
```javascript
if (error.name === 'AbortError') {
    throw new APIError(
        `Request timeout after ${timeout}ms`,
        408,
        'TimeoutError'
    );
}
```

---

## 🛡️ Error Handling

### Типы ошибок и их обработка

#### 1. NetworkError (нет соединения)
```javascript
status: null
code: 'NetworkError'
getUserMessage() → "Нет соединения с сервером. Проверьте интернет-соединение."
```
**Retry**: ✅ Да (3 попытки)

#### 2. TimeoutError (превышено время)
```javascript
status: 408
code: 'TimeoutError'
getUserMessage() → "Превышено время ожидания. Попробуйте еще раз."
```
**Retry**: ✅ Да (3 попытки)

#### 3. ValidationError (4xx)
```javascript
status: 422
code: 'ValidationError'
getUserMessage() → "year: Year must be >= 1990" // от сервера
```
**Retry**: ❌ Нет (ошибка клиента)

#### 4. ServerError (5xx)
```javascript
status: 500
code: 'ServerError'
getUserMessage() → "Ошибка сервера. Попробуйте позже."
```
**Retry**: ❌ Нет (сервер уже получил запрос)

---

## 📝 FastAPI Error Parsing

### Формат ответа FastAPI
```json
{
  "detail": "Year must be >= 1990"
}
```
или
```json
{
  "detail": [
    {"loc": ["body", "year"], "msg": "Year must be >= 1990"},
    {"loc": ["body", "price"], "msg": "Price must be > 0"}
  ]
}
```

### Парсинг в APIClient
```javascript
parseErrorResponse(response) {
    const data = await response.json();
    if (typeof data.detail === 'string') {
        return { message: data.detail };
    } else if (Array.isArray(data.detail)) {
        // Pydantic validation errors
        const errors = data.detail.map(err => 
            `${err.loc.join('.')}: ${err.msg}`
        ).join(', ');
        return { message: errors, details: data.detail };
    }
}
```

---

## 🔄 Integration Changes

### index.html - До
```javascript
class SecureAPI {
    // 125 строк кода
    constructor() { /* ... */ }
    resolveBaseURL() { /* ... */ }
    fetchWithRetry() { /* ... */ }
    get(path) { /* ... */ }
    post(path, data) { /* ... */ }
}

const api = new SecureAPI();
const result = await api.post(API_ENDPOINTS.CALCULATE, requestData);
```

### index.html - После
```javascript
import { api, APIError } from '/static/js/modules/api.js';

// api уже создан как singleton
const result = await api.calculate(requestData);

// Улучшенная обработка ошибок
if (error instanceof APIError) {
    errorMessage = error.getUserMessage();
    console.error('API Error details:', error.toLogFormat());
}
```

**Результат**: -125 строк в index.html, +481 строк в модуле api.js

---

## 🧪 Testing (`tests/manual/test_api_client.html`)

### 8 интерактивных тестов

#### 1️⃣ Basic GET Request
- Тест: `api.getMeta()`
- Проверка: успешный запрос возвращает метаданные

#### 2️⃣ Basic POST Request
- Тест: `api.calculate({...})`
- Проверка: расчёт с валидными данными

#### 3️⃣ Validation Error (4xx)
- Тест: `api.calculate({ year: 1800, engine_cc: -1000 })`
- Проверка: APIError с ValidationError, getUserMessage()

#### 4️⃣ Network Error
- Тест: `api.get('/api/nonexistent-endpoint')`
- Проверка: 404 обрабатывается как ServerError

#### 5️⃣ Timeout Test
- Тест: `new APIClient({ timeout: 100 }).getMeta()`
- Проверка: короткий timeout → TimeoutError
- **Требует**: DevTools → Network → Throttling → Slow 3G

#### 6️⃣ Retry Test
- Тест: `api.getMeta()` с прерыванием сети
- Проверка: retry логи в Console
- **Инструкция**: Отключить интернет на 2-3 секунды

#### 7️⃣ API Methods
- Тесты: `getMeta()`, `getRates()`, `refreshRates()`
- Проверка: все специфичные методы работают

#### 8️⃣ Error Types
- Тест: Создание всех типов APIError
- Проверка: все методы (isNetworkError, isTimeoutError, etc.)

### UI Features
- ✅ Цветовая индикация (🟢 success, 🔴 error, 🟡 loading)
- ✅ Display config (RETRY_COUNT, TIMEOUT, baseURL)
- ✅ Инструкции для каждого теста
- ✅ JSON pretty-print для результатов

---

## 📊 Metrics

### Code Reduction
- **index.html**: -125 строк (SecureAPI удалён)
- **api.js**: +481 строк (новый модуль)
- **Net change**: +356 строк (но с лучшей структурой)

### Test Coverage
- ✅ 8 тестовых сценариев
- ✅ Все типы ошибок покрыты
- ✅ Retry/timeout тестируются вручную

### Error Messages
- ✅ 4 типа ошибок с понятными сообщениями
- ✅ FastAPI error parsing
- ✅ Structured logging

---

## 🎯 Benefits

### 1. Reliability
- Автоматический retry на сетевых ошибках
- Exponential backoff предотвращает DDOS
- Timeout предотвращает бесконечное ожидание

### 2. User Experience
- Понятные сообщения об ошибках
- Не показываем технические детали
- Автоматическое восстановление при сбоях

### 3. Developer Experience
- Централизованная HTTP логика
- Типизированные ошибки (instanceof APIError)
- Structured logging для отладки
- Clean API (api.calculate() вместо api.post('/api/calculate'))

### 4. Maintainability
- Модульная структура (481 строк в отдельном файле)
- Единый источник HTTP логики
- Легко добавить новые методы
- Легко изменить retry/timeout конфигурацию

### 5. Testability
- Изолированный модуль
- Mock-friendly (можно заменить api singleton)
- Manual test suite для проверки

---

## 🔗 Synchronization с Backend

### API Endpoints
```javascript
// constants.js
API_ENDPOINTS = {
    CALCULATE: '/api/calculate',
    META: '/api/meta',
    RATES: '/api/rates',
    REFRESH_RATES: '/api/rates/refresh',
}

// api.js
api.calculate() → POST /api/calculate
api.getMeta() → GET /api/meta
api.getRates() → GET /api/rates
api.refreshRates() → POST /api/rates/refresh
```

### Error Responses
```python
# FastAPI
raise HTTPException(status_code=422, detail="Year must be >= 1990")

# APIClient парсит в:
APIError {
    status: 422,
    code: 'ValidationError',
    message: "Year must be >= 1990"
}
```

---

## 📚 Documentation Updates

### 1. rpg.yaml
- ✅ Добавлен SPRINT_5 в recent_changes
- ✅ Обновлён webapp structure (api.js ✅)
- ✅ Обновлён refactoring_status → SPRINT_5_COMPLETED
- ✅ Добавлены synchronization точки (APIClient ↔ Backend)
- ✅ next_stage → SPRINT_6_UI_MODULE

### 2. webapp_refactoring_checklist.md
- ✅ Этап 5 отмечен как завершённый (✅)
- ✅ Все подзадачи выполнены (15/15)
- ✅ Время фактическое: 2 часа
- ✅ Дата завершения: December 5, 2025

### 3. CHANGELOG_georgia.md
- ✅ Добавлен раздел SPRINT 5
- ✅ Описание всех изменений
- ✅ Benefits, Synchronization, Testing

---

## 🚀 Next Steps (SPRINT 6: UI Module)

### Planned
1. Создать `app/webapp/js/modules/ui.js`:
   - `showLoading(show, message)`
   - `showError(message, type)`
   - `hideError()`
   - `showResult()`
   - `hideResult()`
   - Tab management

2. Извлечь UI логику из index.html (100+ строк)

3. Тесты в `tests/manual/test_ui.html`

---

## ✅ Checklist

- [x] Создан api.js с APIClient и APIError
- [x] Реализован retry с exponential backoff
- [x] Реализован timeout через AbortController
- [x] Парсинг FastAPI {"detail": "..."}
- [x] 4 типа ошибок с getUserMessage()
- [x] Специфичные методы (calculate, getMeta, getRates, refreshRates)
- [x] Structured logging (toLogFormat, timestamp)
- [x] Обновлён index.html (удалён SecureAPI)
- [x] Улучшена обработка ошибок в calculateCost()
- [x] Улучшена обработка ошибок в loadMetaData()
- [x] Создан test_api_client.html (8 тестов)
- [x] Обновлён rpg.yaml
- [x] Обновлён webapp_refactoring_checklist.md
- [x] Обновлён CHANGELOG_georgia.md
- [x] Нет ошибок в get_errors

---

## 🎉 Sprint 5 Complete!

**Статус**: ✅ ЗАВЕРШЕНО  
**Дата**: December 5, 2025  
**Результат**: Robust HTTP client with retry, timeout, and improved error handling

Готов к Sprint 6: UI Module 🚀

