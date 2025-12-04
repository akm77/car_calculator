# WebApp Modules Dependency Graph

```
                            Топологический порядок реализации
                            (читать снизу вверх ↑)
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  10. index.html                                                          │
│      └─ Минимальная обёртка, импортирует только main logic              │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                     ↑
                                     │
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  9. calculator.js (CalculatorController)                                 │
│     └─ Оркестратор: связывает API, Validator, UI, Results, Telegram     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                     ↑
                 ┌───────────────────┼───────────────────┐
                 │                   │                   │
┌────────────────▼────────┐  ┌──────▼───────┐  ┌───────▼──────────┐
│                         │  │              │  │                  │
│  7. results.js          │  │  6. ui.js    │  │  8. telegram.js  │
│     (ResultsRenderer)   │  │     (UI)     │  │     (существует) │
│                         │  │              │  │                  │
└─────────────────────────┘  └──────────────┘  └──────────────────┘
          ↑                         ↑
          │                         │
    ┌─────┴──────┐            ┌─────┴──────┐
    │            │            │            │
    │  formatters│            │   dom.js   │
    │            │            │            │
    └────────────┘            └────────────┘
                                     
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  5. api.js (APIClient)                                                   │
│     └─ HTTP client с retry, timeout, error handling                      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                     ↑
                                     │
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  4. validator.js (FormValidator)                                         │
│     └─ Валидация форм и полей                                           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                     ↑
                 ┌───────────────────┼───────────────────┐
                 │                   │                   │
┌────────────────▼────────┐  ┌──────▼───────┐  ┌───────▼──────────┐
│                         │  │              │  │                  │
│  3a. messages.js        │  │ 3b. constants│  │  2a. formatters  │
│      (Messages)         │  │   (Constraints│  │      .js         │
│                         │  │    API_...)   │  │                  │
└─────────────────────────┘  └──────────────┘  └──────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  2b. dom.js                                                              │
│      └─ show/hide/setText/debounce helpers                               │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  1. CSS (variables.css, base.css, components.css, telegram.css)         │
│     └─ Независимые стили, первыми выносятся                             │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Зависимости между модулями

```
calculator.js
├── api.js
│   └── constants.js (API_ENDPOINTS, API_CONFIG)
├── validator.js
│   ├── constants.js (Constraints)
│   └── messages.js (Messages.errors)
├── ui.js
│   ├── dom.js (show, hide, setText)
│   └── messages.js (Messages.buttons)
├── results.js
│   ├── formatters.js (formatNumber, getAgeCategory)
│   ├── dom.js (setText, setContent)
│   └── messages.js (Messages.labels)
└── telegram.js (уже существует)
```

## Слои архитектуры

```
┌─────────────────────────────────────────────┐
│          PRESENTATION LAYER                 │
│  (index.html, CSS, UI components)           │
└─────────────────────────────────────────────┘
                    ↓ events
┌─────────────────────────────────────────────┐
│       ORCHESTRATION LAYER                   │
│  (calculator.js - CalculatorController)     │
└─────────────────────────────────────────────┘
                    ↓ calls
┌─────────────────────────────────────────────┐
│        BUSINESS LOGIC LAYER                 │
│  (validator.js, results.js, telegram.js)    │
└─────────────────────────────────────────────┘
                    ↓ uses
┌─────────────────────────────────────────────┐
│          DATA ACCESS LAYER                  │
│        (api.js - APIClient)                 │
└─────────────────────────────────────────────┘
                    ↓ HTTP
┌─────────────────────────────────────────────┐
│           BACKEND API                       │
│    (FastAPI /api/calculate, etc.)           │
└─────────────────────────────────────────────┘

      CROSS-CUTTING CONCERNS
┌─────────────────────────────────────────────┐
│  utils/    - formatters.js, dom.js          │
│  config/   - messages.js, constants.js      │
└─────────────────────────────────────────────┘
```

## Порядок реализации (RPG топология)

**Уровень 0: Нет зависимостей**
- CSS файлы
- utils/formatters.js
- utils/dom.js
- config/messages.js
- config/constants.js

**Уровень 1: Зависят только от Уровня 0**
- modules/api.js (зависит от constants)
- modules/validator.js (зависит от constants, messages)

**Уровень 2: Зависят от Уровней 0-1**
- modules/ui.js (зависит от dom, messages)
- modules/results.js (зависит от formatters, dom, messages)

**Уровень 3: Зависят от Уровней 0-2**
- modules/calculator.js (зависит от api, validator, ui, results, telegram)

**Уровень 4: Финальная интеграция**
- index.html (импортирует calculator + telegram)

## Интерфейсы модулей (API контракты)

### formatters.js
```javascript
export function formatNumber(num: number | null): string
export function formatCurrency(amount: number, currency: string): string
export function getAgeCategory(category: string): string
```

### dom.js
```javascript
export function show(element: string | HTMLElement): void
export function hide(element: string | HTMLElement): void
export function setText(elementId: string, text: string): void
export function setContent(elementId: string, html: string): void
export function debounce(fn: Function, delay: number): Function
```

### validator.js
```javascript
export class FormValidator {
    constructor(constraints: Constraints)
    validate(formData: FormData): ValidationResult
    validateField(name: string, value: any): string | null
}
```

### api.js
```javascript
export class APIClient {
    constructor(baseURL: string)
    async calculate(request: CalculationRequest): Promise<CalculationResult>
    async getMeta(): Promise<MetaData>
    async getRates(): Promise<RatesData>
}

export class APIError extends Error {
    status: number
    details: any
}
```

### ui.js
```javascript
export class UI {
    showError(message: string): void
    hideError(): void
    showLoading(text?: string): void
    hideLoading(): void
    showResult(): void
    hideResult(): void
}
```

### results.js
```javascript
export class ResultsRenderer {
    constructor(metaData: MetaData | null)
    render(result: CalculationResult): void
    renderTotal(breakdown: CostBreakdown): void
    renderBreakdown(breakdown: CostBreakdown): void
    renderMeta(meta: CalculationMeta, request: CalculationRequest): void
}
```

### calculator.js
```javascript
export class CalculatorController {
    constructor(telegram: TelegramWebAppHelper, metaData: MetaData)
    setCountry(country: string): void
    setFreightType(freightType: string): void
    async handleSubmit(form: HTMLFormElement): Promise<void>
    updateTelegramButton(): void
}
```

## Dataflow (как данные текут через систему)

```
User Input (Form)
      ↓
CalculatorController.handleSubmit()
      ↓
FormValidator.validate(formData)
      ↓ (if valid)
CalculatorController.buildRequest()
      ↓
APIClient.calculate(request)
      ↓ HTTP POST /api/calculate
Backend (FastAPI)
      ↓ HTTP Response
CalculationResult
      ↓
ResultsRenderer.render(result)
      ↓
DOM Updates (show result card)
      ↓
User sees result
```

## Преимущества этой архитектуры

✅ **Однонаправленный dataflow** - данные текут сверху вниз  
✅ **Явные зависимости** - каждый модуль знает от кого зависит  
✅ **Тестируемость** - каждый модуль можно тестировать изолированно  
✅ **Замена компонентов** - легко заменить validator или api client  
✅ **Масштабируемость** - легко добавить новые модули  

## Антипаттерны, которых избегаем

❌ **Circular dependencies** - модули не ссылаются друг на друга циклично  
❌ **Global state** - состояние инкапсулировано в CalculatorController  
❌ **God object** - каждый модуль делает одну вещь хорошо  
❌ **Tight coupling** - модули общаются через интерфейсы  
❌ **Hidden dependencies** - все зависимости явные (import)  

