# ПРОМПТ: СПРИНТ 6 — Фронтенд (WebApp)

## 🎭 РОЛЬ МОДЕЛИ
Ты — **Frontend Engineer** с экспертизой в Vanilla JavaScript, модульной архитектуре, Telegram WebApp API и accessibility (a11y).

---

## 📘 МЕТОДОЛОГИЯ
Используй **Repository Planning Graph (RPG)** — прочти `docs/rpg_intro.txt`.

**Ключевые принципы для этого спринта:**
1. **Модульность** — используй существующие модули (validator.js, constants.js), не дублируй код
2. **Топологический порядок** — сначала constants/messages, затем validator, затем UI
3. **Инкрементальная валидация** — после каждого изменения открывай WebApp и проверяй

---

## 📊 ГРАФ ПРОЕКТА
**Обязательно обнови** после завершения спринта: `docs/rpg.yaml`

**Добавь в recent_changes:**
```yaml
- date: "2025-12-08"
  description: "SPRINT 6 завершён: Добавлено поле 'Мощность двигателя (л.с.)' в WebApp форму (после engineCc), обновлены constants.js (ENGINE_POWER_HP_MIN/MAX, CONVERSION_FACTORS), validator.js (валидация engine_power_hp), calculateCost() (передача в API), displayResult() (отображение мощности и коэффициента), manual test проверен"
```

---

## 🎯 ЦЕЛЬ СПРИНТА
Интегрировать новое поле `engine_power_hp` в WebApp интерфейс:
1. Добавить HTML-поле в форму
2. Обновить константы и валидацию
3. Передать значение в API при расчёте
4. Отобразить результаты (мощность в кВт, коэффициент утильсбора)
5. Протестировать в Telegram WebApp

---

## 📚 ИСТОЧНИКИ ПРАВДЫ

### Первичные источники (читай ОБЯЗАТЕЛЬНО)
1. **План работ**: `docs/REFACTORING_PLAN.md` (Этап 6, задачи 6.1-6.5)
2. **Текущий HTML**: `app/webapp/index.html` (форма калькулятора)
3. **Константы**: `app/webapp/js/config/constants.js`
4. **Валидатор**: `app/webapp/js/modules/validator.js`
5. **API endpoint**: Результат Спринта 5 — GET /api/meta возвращает constraints

### Вторичные источники (для контекста)
6. **Messages**: `app/webapp/js/config/messages.js` (если нужны новые тексты)
7. **CSS**: `app/webapp/css/components.css` (стили формы)
8. **Backend модели**: `app/calculation/models.py` (CalculationMeta — новые поля)

### Проблема «Lost in the Middle»
⚠️ **Фокусируйся на малых частях:**
- Сначала только HTML → проверь рендеринг
- Затем только constants.js → проверь import
- Затем только validator.js → проверь валидацию
- Не редактируй весь index.html за раз (1548 строк!)

---

## ✅ КРИТЕРИИ ДОСТИЖЕНИЯ ЦЕЛИ

### Обязательные (Must Have)
- [ ] **Поле в форме** — HTML input `enginePowerHp` после поля `engineCc`
- [ ] **Константы обновлены** — `Constraints.ENGINE_POWER_HP_MIN/MAX` и `CONVERSION_FACTORS` в constants.js
- [ ] **Валидация работает** — FormValidator.validateField('enginePowerHp') возвращает ошибки при невалидных значениях
- [ ] **API интеграция** — calculateCost() передаёт `engine_power_hp` в requestData
- [ ] **Отображение результата** — displayResult() показывает мощность в кВт и коэффициент утильсбора
- [ ] **Manual test проходит** — форма заполняется, расчёт работает, результат корректен

### Проверочные (Should Have)
- [ ] **Real-time валидация** — ошибки показываются при вводе (onBlur/onChange)
- [ ] **Accessibility** — label связан с input через for/id, aria-required="true"
- [ ] **Help text** — подсказка о конвертации (1 л.с. = 0.7355 кВт)
- [ ] **Unit suffix** — "л.с." отображается справа от input (класс .input-with-unit)

### Дополнительные (Nice to Have)
- [ ] **Tooltip** — при наведении на "?" показывается объяснение
- [ ] **Auto-fill** — при вводе engine_cc предлагается типичная мощность
- [ ] **Visual feedback** — Telegram haptic feedback при успешном вводе

---

## 🔍 ЗАДАЧИ (в порядке выполнения)

### Задача 6.1: Добавить HTML-поле "Мощность двигателя"

**Файл:** `app/webapp/index.html`

**Место вставки:** После блока `<div class="form-group">` с `id="engineCc"`

**Код для добавления:**
```html
<!-- Мощность двигателя (NEW 2025) -->
<div class="form-group">
    <label for="enginePowerHp">
        <span class="label-text">Мощность двигателя</span>
        <span class="required-mark" aria-label="обязательное поле">*</span>
    </label>
    <div class="input-with-unit">
        <input 
            type="number" 
            id="enginePowerHp" 
            name="enginePowerHp"
            min="1" 
            max="1500" 
            step="1"
            required
            aria-required="true"
            aria-describedby="enginePowerHpHelp"
            placeholder="150"
        >
        <span class="unit">л.с.</span>
    </div>
    <small id="enginePowerHpHelp" class="help-text">
        Будет конвертировано в кВт (1 л.с. = 0.7355 кВт)
    </small>
    <div class="field-error" id="enginePowerHpError" role="alert"></div>
</div>
```

**Критерий готовности:** Поле отображается в браузере между "Объём двигателя" и следующим полем

---

### Задача 6.2: Обновить constants.js

**Файл:** `app/webapp/js/config/constants.js`

**Изменения:**
```javascript
// ...existing code...

/**
 * Ограничения валидации (синхронизированы с backend models.py)
 */
export const Constraints = {
    YEAR_MIN: 1990,
    YEAR_MAX: new Date().getFullYear(),
    ENGINE_CC_MIN: 500,
    ENGINE_CC_MAX: 10000,
    
    // NEW 2025: Мощность двигателя
    ENGINE_POWER_HP_MIN: 1,
    ENGINE_POWER_HP_MAX: 1500,
    
    PURCHASE_PRICE_MIN: 1000,
    PURCHASE_PRICE_MAX: 100000000
};

// NEW 2025: Коэффициенты конвертации
/**
 * Коэффициенты для конвертации единиц измерения.
 * Синхронизированы с GET /api/meta response.
 */
export const CONVERSION_FACTORS = {
    HP_TO_KW: 0.7355,      // лошадиные силы → киловатты
    KW_TO_HP: 1.35962      // киловатты → лошадиные силы (обратная)
};

// ...existing code...
```

**Критерий готовности:** `import { Constraints, CONVERSION_FACTORS } from './constants.js'` работает в других модулях

---

### Задача 6.3: Обновить validator.js

**Файл:** `app/webapp/js/modules/validator.js`

**Изменения:**
```javascript
// ...existing imports...
import { Constraints } from '../config/constants.js';

export class FormValidator {
    // ...existing code...
    
    /**
     * Валидация отдельного поля.
     * @param {string} fieldName - Имя поля
     * @param {any} value - Значение поля
     * @returns {string|null} Сообщение об ошибке или null
     */
    validateField(fieldName, value) {
        switch (fieldName) {
            // ...existing cases...
            
            case 'engineCc':
                // ...existing validation...
                break;
            
            // NEW 2025: Валидация мощности двигателя
            case 'enginePowerHp': {
                const power = parseInt(value, 10);
                
                if (isNaN(power)) {
                    return Messages.errors.enginePowerHpRequired || 'Введите мощность двигателя в л.с.';
                }
                
                if (power < Constraints.ENGINE_POWER_HP_MIN) {
                    return `Минимальная мощность: ${Constraints.ENGINE_POWER_HP_MIN} л.с.`;
                }
                
                if (power > Constraints.ENGINE_POWER_HP_MAX) {
                    return `Максимальная мощность: ${Constraints.ENGINE_POWER_HP_MAX} л.с.`;
                }
                
                return null; // валидация пройдена
            }
            
            // ...existing cases...
            
            default:
                return null;
        }
    }
    
    /**
     * Возвращает constraints для конкретного поля.
     * @param {string} fieldName - Имя поля
     * @returns {Object} Constraints объект
     */
    getFieldConstraints(fieldName) {
        const constraints = {
            // ...existing fields...
            
            enginePowerHp: {  // NEW
                min: Constraints.ENGINE_POWER_HP_MIN,
                max: Constraints.ENGINE_POWER_HP_MAX,
                step: 1,
                required: true,
                type: 'number'
            },
            
            // ...existing fields...
        };
        
        return constraints[fieldName] || {};
    }
    
    // ...existing methods...
}
```

**Критерий готовности:** 
```javascript
const validator = new FormValidator();
console.log(validator.validateField('enginePowerHp', 0));    // "Минимальная мощность: 1 л.с."
console.log(validator.validateField('enginePowerHp', 2000)); // "Максимальная мощность: 1500 л.с."
console.log(validator.validateField('enginePowerHp', 150));  // null (OK)
```

---

### Задача 6.4: Обновить messages.js (если нужно)

**Файл:** `app/webapp/js/config/messages.js`

**Проверь наличие сообщений:**
```javascript
export const Messages = {
    errors: {
        // ...existing errors...
        enginePowerHpRequired: 'Укажите мощность двигателя',  // добавь если отсутствует
    },
    labels: {
        // ...existing labels...
        enginePowerHp: 'Мощность двигателя (л.с.)',  // опционально
    },
    breakdown: {
        // ...existing...
        enginePowerKw: 'Мощность (кВт)',             // NEW: для отображения в результатах
        utilizationCoefficient: 'Коэффициент утильсбора',  // NEW
    }
};
```

**Критерий готовности:** Все тексты для нового поля есть в messages.js

---

### Задача 6.5: Интегрировать в calculateCost()

**Файл:** `app/webapp/index.html` (функция `calculateCost()`)

**Найди блок формирования requestData:**
```javascript
async function calculateCost() {
    // ...existing code: ui.showLoading(), formData = new FormData()...
    
    // Формирование данных запроса
    const requestData = {
        country: formData.get('country'),
        year: parseInt(formData.get('year')),
        engine_cc: parseInt(formData.get('engineCc')),
        engine_power_hp: parseInt(formData.get('enginePowerHp')), // NEW: добавь эту строку
        purchase_price: parseFloat(formData.get('purchasePrice')),
        currency: formData.get('currency'),
        vehicle_type: formData.get('vehicleType') || 'M1',
        freight_type: formData.get('freightType') || 'container'
    };
    
    // ...existing code: validation, API call...
}
```

**Критерий готовности:** При отправке формы в Network tab видно `"engine_power_hp": 150` в payload

---

### Задача 6.6: Обновить displayResult()

**Файл:** `app/webapp/index.html` (функция `displayResult(result)`)

**Найди блок отображения meta-информации:**
```javascript
function displayResult(result) {
    // ...existing code для breakdown...
    
    // Метаинформация
    let metaHtml = `
        <div class="meta-item">
            <span class="meta-label">Возраст авто:</span>
            <span class="meta-value">${formatters.getAgeCategory(result.meta.age_category)}</span>
        </div>
    `;
    
    // NEW 2025: Отображение мощности и конвертации
    if (result.meta.engine_power_hp && result.meta.engine_power_kw) {
        metaHtml += `
            <div class="meta-item">
                <span class="meta-label">Мощность двигателя:</span>
                <span class="meta-value">
                    ${result.meta.engine_power_hp} л.с. 
                    <span class="text-muted">(${result.meta.engine_power_kw.toFixed(2)} кВт)</span>
                </span>
            </div>
        `;
    }
    
    // NEW 2025: Коэффициент утилизационного сбора
    if (result.meta.utilization_coefficient !== null && result.meta.utilization_coefficient !== undefined) {
        metaHtml += `
            <div class="meta-item">
                <span class="meta-label">Коэффициент утильсбора:</span>
                <span class="meta-value">${result.meta.utilization_coefficient}</span>
                <small class="help-text">
                    Базовая ставка 20 000 ₽ × коэффициент = ${formatters.formatNumber(result.breakdown.utilization_fee_rub)} ₽
                </small>
            </div>
        `;
    }
    
    // ...existing code: warnings, total...
}
```

**Критерий готовности:** После расчёта отображаются новые поля (мощность и коэффициент)

---

### Задача 6.7: Добавить real-time валидацию (опционально)

**Файл:** `app/webapp/index.html`

**Найди блок инициализации валидации:**
```javascript
// При загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // ...existing code...
    
    // NEW: Real-time валидация для enginePowerHp
    const enginePowerHpInput = document.getElementById('enginePowerHp');
    if (enginePowerHpInput) {
        enginePowerHpInput.addEventListener('blur', function() {
            const error = formValidator.validateField('enginePowerHp', this.value);
            const errorDiv = document.getElementById('enginePowerHpError');
            
            if (error) {
                this.classList.add('error');
                errorDiv.textContent = error;
                errorDiv.style.display = 'block';
            } else {
                this.classList.remove('error');
                errorDiv.textContent = '';
                errorDiv.style.display = 'none';
            }
        });
    }
    
    // ...existing code...
});
```

**Критерий готовности:** При вводе невалидного значения (0, 2000) и потере фокуса появляется красная рамка и ошибка

---

## 🧪 ТЕСТИРОВАНИЕ

### Manual Testing Checklist

**1. Проверка отображения формы:**
```bash
# Запусти сервер
python -m app.main

# Открой в браузере
open http://localhost:8000/web/
```

- [ ] Поле "Мощность двигателя" видно после "Объём двигателя"
- [ ] Placeholder "150" отображается
- [ ] Единица измерения "л.с." справа от input
- [ ] Help text о конвертации виден

**2. Проверка валидации:**
- [ ] Введи `0` → должна появиться ошибка "Минимальная мощность: 1 л.с."
- [ ] Введи `2000` → "Максимальная мощность: 1500 л.с."
- [ ] Введи `150` → ошибка исчезает
- [ ] Оставь пустым → "Введите мощность двигателя"

**3. Проверка расчёта:**
Заполни форму:
- Страна: Япония
- Год: 2022 (lt3)
- Объём: 1500 cc
- **Мощность: 110 л.с.** ← NEW
- Цена: 2,500,000 JPY

Нажми "Рассчитать"

Проверь результат:
- [ ] Расчёт выполнился без ошибок
- [ ] В блоке метаинформации есть "Мощность: 110 л.с. (80.91 кВт)"
- [ ] Есть "Коэффициент утильсбора: 0.26" (или другой по таблице)
- [ ] Утилизационный сбор = 5,200 ₽ (20,000 × 0.26)

**4. Проверка в Telegram WebApp:**
```bash
# Запусти бота
python -m app.bot.main
```

- [ ] Открой WebApp через кнопку в боте
- [ ] Поле "Мощность" отображается корректно
- [ ] Тач-валидация работает (tap вне input → проверка)
- [ ] Haptic feedback срабатывает при успехе/ошибке

---

### Automated Testing (опционально)

**Создай:** `tests/manual/test_frontend_engine_power.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>Test: Engine Power Field</title>
    <script type="module">
        import { FormValidator } from '../app/webapp/js/modules/validator.js';
        import { Constraints } from '../app/webapp/js/config/constants.js';
        
        const validator = new FormValidator();
        
        console.assert(validator.validateField('enginePowerHp', 0) !== null, 'Test 1: Reject 0');
        console.assert(validator.validateField('enginePowerHp', 2000) !== null, 'Test 2: Reject 2000');
        console.assert(validator.validateField('enginePowerHp', 150) === null, 'Test 3: Accept 150');
        
        console.log('✅ All frontend tests passed');
    </script>
</head>
<body>
    <h1>Check Console</h1>
</body>
</html>
```

---

## 📝 ДОКУМЕНТАЦИЯ

### Комментарии в коде
```javascript
// app/webapp/index.html

/**
 * calculateCost() — Выполнение расчёта через API
 * 
 * NEW in v2.0 (2025-12-08):
 * - Добавлено поле engine_power_hp (обязательное)
 * - Валидация через FormValidator
 * - Отображение мощности в кВт и коэффициента утильсбора
 */
async function calculateCost() {
    // ...
}
```

### Обновление rpg.yaml
```yaml
files:
  - name: "index.html"
    parent_module: "app_webapp"
    description: "Главная страница калькулятора (форма с полем engine_power_hp, calculateCost передаёт в API, displayResult отображает мощность и коэффициент)"

components:
  - name: "FormValidator.validateField('enginePowerHp')"
    parent_file: "validator.js"
    type: "method"
    description: "Валидация мощности двигателя (1-1500 л.с.)"
    testable: true
    test_priority: "high"

recent_changes:
  - date: "2025-12-08"
    description: "SPRINT 6 завершён: Добавлено поле engine_power_hp в WebApp (HTML, validator, constants, calculateCost, displayResult), real-time валидация, отображение мощности в кВт и коэффициента утильсбора"
```

---

## 🚨 ПРОБЛЕМЫ И РЕШЕНИЯ

### Проблема: Поле не отображается
**Причина:** Неправильное место вставки HTML

**Решение:**
1. Найди `<input id="engineCc">` в index.html
2. Найди закрывающий тег `</div>` этого form-group
3. Вставь новый блок ПОСЛЕ этого </div>

### Проблема: Валидация не срабатывает
**Причина:** FormValidator не инициализирован

**Решение:**
```javascript
// Проверь, что в index.html есть:
import { FormValidator } from './js/modules/validator.js';
const formValidator = new FormValidator();
```

### Проблема: API возвращает 422 Validation Error
**Причина:** Backend ожидает engine_power_hp, но не получает

**Решение:**
1. Открой DevTools → Network → Calculate request
2. Проверь Payload: есть ли поле `engine_power_hp`?
3. Если нет — проверь `formData.get('enginePowerHp')` (case-sensitive!)

### Проблема: Мощность не отображается в результате
**Причина:** Backend не возвращает meta.engine_power_kw

**Решение:**
1. Проверь Response в Network tab
2. Если `meta.engine_power_kw` === null → проблема в backend (Спринт 3)
3. Добавь fallback:
   ```javascript
   const powerKw = result.meta.engine_power_kw || (result.meta.engine_power_hp * 0.7355);
   ```

---

## ⏱️ ВРЕМЯ ВЫПОЛНЕНИЯ
**Оценка:** 3-4 часа

**Breakdown:**
- Задача 6.1: 20 минут (HTML)
- Задача 6.2: 10 минут (constants)
- Задача 6.3: 30 минут (validator)
- Задача 6.4: 10 минут (messages)
- Задача 6.5: 15 минут (calculateCost)
- Задача 6.6: 30 минут (displayResult)
- Задача 6.7: 20 минут (real-time validation)
- Тестирование: 60 минут (manual + Telegram WebApp)

---

## 📞 NEXT STEPS
После завершения спринта:
1. **Обнови rpg.yaml** (добавь recent_changes)
2. **Коммит изменений:**
   ```bash
   git add app/webapp/index.html app/webapp/js/ docs/rpg.yaml
   git commit -m "feat(webapp): add engine_power_hp field with validation and result display"
   ```
3. **Переходи к Спринту 7** (Telegram Bot) — см. `docs/sprint_prompts/SPRINT_7_TELEGRAM_BOT.md`

---

## 🔗 СВЯЗАННЫЕ ФАЙЛЫ
- `docs/REFACTORING_PLAN.md` — полный план (Этап 6)
- `app/webapp/index.html` — главный файл (форма и логика)
- `app/webapp/js/config/constants.js` — константы
- `app/webapp/js/modules/validator.js` — валидация
- `app/webapp/js/config/messages.js` — тексты
- `app/calculation/models.py` — backend модели (CalculationMeta)

---

**Автор промпта:** RPG Architect  
**Версия:** 1.0  
**Дата:** 2025-12-08

