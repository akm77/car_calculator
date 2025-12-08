# 📖 ПОДРОБНОЕ ОБЪЯСНЕНИЕ: Как получаем результат расчета от API

**Дата**: 8 декабря 2025 (обновлено для v2.0)  
**Файл**: `app/webapp/index.html`  
**API Endpoint**: `POST /api/calculate`

> **⚠️ ВАЖНО (v2.0):** С версии 2.0.0 добавлено **обязательное поле** `engine_power_hp` (1-1500 л.с.)  
> См. [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) для деталей миграции.

---

## 🔄 ПОЛНЫЙ ЖИЗНЕННЫЙ ЦИКЛ РАСЧЕТА

### 1️⃣ Пользователь нажимает "Рассчитать стоимость"

```javascript
// index.html, строка 657
document.getElementById('calculatorForm').addEventListener('submit', function(e) {
    e.preventDefault();  // Останавливаем стандартную отправку формы
    calculateCost();     // Вызываем нашу функцию
});
```

---

### 2️⃣ Функция `calculateCost()` - подготовка и отправка запроса

```javascript
// index.html, строки 908-956
async function calculateCost() {
    // ============================================================
    // ШАГ 1: ВАЛИДАЦИЯ ПРЕДУСЛОВИЙ
    // ============================================================
    
    // Проверка: выбрана ли страна?
    if (!selectedCountry) {
        ui.showError(Messages.errors.NO_COUNTRY);
        return;  // ❌ СТОП: нет страны
    }
    
    // Проверка: валидны ли данные формы?
    if (!validateForm()) return;  // ❌ СТОП: невалидные данные
    
    // ============================================================
    // ШАГ 2: СБОР ДАННЫХ ИЗ ФОРМЫ
    // ============================================================
    
    const formData = new FormData(document.getElementById('calculatorForm'));
    const requestData = {
        country: selectedCountry,                              // 'georgia', 'japan', etc.
        year: parseInt(formData.get('year')),                  // 2022
        engine_cc: parseInt(formData.get('engineCc')),         // 1500
        engine_power_hp: parseInt(formData.get('enginePowerHp')), // 110 ← NEW v2.0
        purchase_price: parseFloat(formData.get('purchasePrice')), // 10000
        currency: formData.get('currency'),                    // 'USD', 'JPY', etc.
        freight_type: selectedFreightType,                     // 'open', 'container'
        vehicle_type: formData.get('vehicleType') || 'M1'      // 'M1' (легковой)
    };
    
    console.log('[calculateCost] Request data:', requestData);
    // Вывод: {country: 'georgia', year: 2022, engine_cc: 1500, engine_power_hp: 110, ...}
    
    // ============================================================
    // ШАГ 3: ПОКАЗЫВАЕМ ИНДИКАТОР ЗАГРУЗКИ
    // ============================================================
    
    ui.showLoading();  // Показываем спиннер
    
    // ============================================================
    // ШАГ 4: ОТПРАВКА ЗАПРОСА К API
    // ============================================================
    
    try {
        telegram.setMainButtonLoading(true);  // Telegram WebApp loading
        
        // ⭐ КЛЮЧЕВОЙ МОМЕНТ: Вызов API
        const result = await api.calculate(requestData);
        
        // ============================================================
        // ШАГ 5: ✅ УСПЕХ - ОТОБРАЖАЕМ РЕЗУЛЬТАТ
        // ============================================================
        
        displayResult(result);  // ← ЭТО ГЛАВНАЯ ФУНКЦИЯ ДЛЯ ОТОБРАЖЕНИЯ
        
        // Telegram WebApp интеграция
        if (telegram.isInTelegram()) {
            telegram.hapticFeedback(HAPTIC_TYPES.MEDIUM);  // Вибрация
            telegram.hideMainButton();
            telegram.showBackButton();
        }
        
    } catch (error) {
        // ============================================================
        // ШАГ 5: ❌ ОШИБКА - ПОКАЗЫВАЕМ СООБЩЕНИЕ
        // ============================================================
        
        console.error('Calculation error:', error);
        
        let errorMessage = Messages.errors.CALCULATION_ERROR;
        if (error instanceof APIError) {
            errorMessage = error.getUserMessage();
            console.error('API Error details:', error.toLogFormat());
        } else {
            errorMessage += ': ' + error.message;
        }
        
        ui.showError(errorMessage);  // Показываем ошибку пользователю
        telegram.hapticFeedback(HAPTIC_TYPES.HEAVY);  // Вибрация ошибки
        
    } finally {
        // ============================================================
        // ШАГ 6: ВСЕГДА СКРЫВАЕМ ИНДИКАТОР ЗАГРУЗКИ
        // ============================================================
        
        ui.hideLoading();  // Скрываем спиннер
        telegram.setMainButtonLoading(false);
    }
}
```

---

### 3️⃣ Модуль API: `api.calculate()` - HTTP запрос

```javascript
// app/webapp/js/modules/api.js
class APIClient {
    async calculate(data) {
        console.log('[APIClient] POST', this.baseURL + '/api/calculate', data);
        
        // Отправка POST запроса
        return this._request('POST', '/api/calculate', data);
    }
    
    async _request(method, endpoint, data) {
        const url = this.baseURL + endpoint;
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new APIError('HTTP_ERROR', response.status, ...);
        }
        
        const result = await response.json();
        console.log('[APIClient] Response received:', result);
        
        return result;  // ← Возвращаем результат в calculateCost()
    }
}
```

---

### 4️⃣ Backend API: FastAPI обрабатывает запрос

```python
# app/api/routes.py
@router.post("/calculate", response_model=CalculationResult)
async def calculate_endpoint(req: CalculationRequest):
    """
    Calculate car import cost
    """
    result = calculate(
        country=req.country,
        year=req.year,
        engine_cc=req.engine_cc,
        purchase_price=req.purchase_price,
        currency=req.currency,
        freight_type=req.freight_type,
        vehicle_type=req.vehicle_type
    )
    
    return result  # ← Возвращает JSON с breakdown и meta
```

---

### 5️⃣ Структура ответа API (JSON)

```json
{
  "breakdown": {
    "purchase_price_rub": 925000.0,      // Цена авто в рублях
    "duties_rub": 185000.0,              // Пошлины
    "utilization_fee_rub": 340000.0,     // Утилизационный сбор
    "customs_services_rub": 5000.0,      // Таможенные услуги
    "era_glonass_rub": 25000.0,          // ЭРА-ГЛОНАСС
    "freight_rub": 150000.0,             // Фрахт
    "country_expenses_rub": 50000.0,     // Расходы в стране покупки
    "company_commission_rub": 20000.0,   // Комиссия компании
    "total_rub": 1700000.0               // 💰 ИТОГО
  },
  "meta": {
    "age_years": 2,                      // Возраст авто
    "age_category": "3_5",               // Категория: от 3 до 5 лет
    "volume_band": "1500-2000",          // Диапазон объема двигателя
    "engine_power_hp": 110,              // ← NEW v2.0: Мощность в л.с.
    "engine_power_kw": 80.91,            // ← NEW v2.0: Мощность в кВт (hp × 0.7355)
    "utilization_coefficient": 0.26,     // ← NEW v2.0: Коэффициент утильсбора
    "customs_value_eur": 9500.0,         // Таможенная стоимость
    "duty_formula_mode": "percent",      // Режим расчета пошлины
    "duty_percent": 0.2,                 // 20% пошлина
    "duty_min_rate_eur_per_cc": 0.5,     // Минимум 0.5 €/см³
    "vehicle_type": "M1",
    "warnings": []                       // Предупреждения (если есть)
  },
  "request": {
    "country": "georgia",
    "year": 2022,
    "engine_cc": 1500,
    "engine_power_hp": 110,              // ← NEW v2.0: ОБЯЗАТЕЛЬНОЕ ПОЛЕ
    "purchase_price": 10000.0,
    "currency": "USD",
    "freight_type": "open",
    "vehicle_type": "M1"
  }
}
```

---

### 6️⃣ Функция `displayResult(result)` - отображение результата

```javascript
// index.html, строки 958-1044
function displayResult(result) {
    console.log('[displayResult] Received result:', result);
    
    // ============================================================
    // ДЕСТРУКТУРИЗАЦИЯ: Извлекаем breakdown и meta из ответа
    // ============================================================
    
    const { breakdown, meta } = result;
    
    // ============================================================
    // 1. ПОКАЗЫВАЕМ ОБЩУЮ СУММУ (вверху карточки)
    // ============================================================
    
    // ✅ ИСПРАВЛЕНО: formatters.formatNumber вместо formatNumber
    document.getElementById('totalAmount').textContent = 
        formatters.formatNumber(breakdown.total_rub) + ' ₽';
    
    // Результат: "1 700 000 ₽" (с пробелами, русский формат)
    
    // ============================================================
    // 2. ФОРМИРУЕМ ДЕТАЛИЗАЦИЮ РАСХОДОВ (breakdown)
    // ============================================================
    
    const breakdownDiv = document.getElementById('breakdown');
    breakdownDiv.innerHTML = '';  // Очищаем предыдущие результаты
    
    const items = [
        { label: 'Цена авто', amount: breakdown.purchase_price_rub },
        { label: 'Расходы в стране', amount: breakdown.country_expenses_rub },
        { label: 'Фрахт', amount: breakdown.freight_rub },
        { label: 'Пошлины', amount: breakdown.duties_rub },
        { label: 'Таможенные услуги', amount: breakdown.customs_services_rub },
        { label: 'Утилизационный сбор', amount: breakdown.utilization_fee_rub },
        { label: 'ЭРА-ГЛОНАСС', amount: breakdown.era_glonass_rub },
        { label: 'Комиссия компании', amount: breakdown.company_commission_rub }
    ];
    
    // Перебираем все статьи расходов
    items.forEach(item => {
        if (item.amount > 0) {  // Показываем только ненулевые
            const div = document.createElement('div');
            div.className = 'breakdown-item';
            
            // ✅ ИСПРАВЛЕНО: formatters.formatNumber
            div.innerHTML = `
                <span class="breakdown-label">${item.label}</span>
                <span class="breakdown-amount">${formatters.formatNumber(item.amount)} ₽</span>
            `;
            
            breakdownDiv.appendChild(div);
        }
    });
    
    // Добавляем итоговую строку
    const totalDiv = document.createElement('div');
    totalDiv.className = 'breakdown-item';
    
    // ✅ ИСПРАВЛЕНО: formatters.formatNumber
    totalDiv.innerHTML = `
        <span class="breakdown-label">Итого</span>
        <span class="breakdown-amount">${formatters.formatNumber(breakdown.total_rub)} ₽</span>
    `;
    
    breakdownDiv.appendChild(totalDiv);
    
    // ============================================================
    // 3. ПОКАЗЫВАЕМ МЕТАДАННЫЕ (возраст, объем, пошлины)
    // ============================================================
    
    const engineDisplay = meta.volume_band !== 'value_brackets' && meta.volume_band !== 'n/a'
        ? meta.volume_band           // "1500-2000"
        : `${result.request.engine_cc} см³`;  // "1500 см³"
    
    const parts = [];
    
    // Страна покупки
    const countryCode = result.request.country || selectedCountry;
    if (countryCode) {
        const countryLabel = getCountryLabel(countryCode);  // "🇬🇪 Грузия"
        parts.push(`<div>Страна: ${countryLabel}</div>`);
    }
    
    // Возраст авто с категорией
    // ✅ ИСПРАВЛЕНО: formatters.getAgeCategory
    parts.push(`<div>Возраст: ${meta.age_years} лет (${formatters.getAgeCategory(meta.age_category)})</div>`);
    // Результат: "Возраст: 2 лет (от 3 до 5 лет)"
    
    // Объем двигателя
    parts.push(`<div>Двигатель: ${engineDisplay}</div>`);
    
    // Таможенная стоимость
    if (meta.customs_value_eur != null) {
        // ✅ ИСПРАВЛЕНО: formatters.formatNumber
        parts.push(`<div>Таможенная стоимость: ${formatters.formatNumber(Math.round(meta.customs_value_eur))} €</div>`);
    }
    
    // Детали пошлины (если процентный режим)
    if (meta.duty_formula_mode === 'percent') {
        if (meta.duty_percent != null) {
            parts.push(`<div>Пошлина: ${Math.round(meta.duty_percent * 100)}% от стоимости (минимум по €/см³)</div>`);
        }
        if (meta.duty_min_rate_eur_per_cc != null) {
            parts.push(`<div>Минимальная ставка: ${meta.duty_min_rate_eur_per_cc} €/см³</div>`);
        }
        if (meta.duty_value_bracket_max_eur != null) {
            // ✅ ИСПРАВЛЕНО: formatters.formatNumber
            parts.push(`<div>Порог стоимости: ${formatters.formatNumber(meta.duty_value_bracket_max_eur)} €</div>`);
        }
    }
    
    // Предупреждения (если есть)
    if (meta.warnings && meta.warnings.length) {
        parts.push('<div style="color:#e74c3c;margin-top:8px;">⚠️ ' + 
            meta.warnings.map(w => w.message).join('<br>⚠️ ') + 
        '</div>');
    }
    
    // Вставляем всё в metaInfo блок
    const metaDiv = document.getElementById('metaInfo');
    metaDiv.innerHTML = parts.join('');
    
    // ============================================================
    // 4. ПОКАЗЫВАЕМ КАРТОЧКУ С РЕЗУЛЬТАТАМИ
    // ============================================================
    
    ui.showResult();  // Делает resultCard видимым с анимацией
    
    // ============================================================
    // 5. СОХРАНЯЕМ РЕЗУЛЬТАТ ДЛЯ SHARING
    // ============================================================
    
    window.lastCalculationResult = result;  // Для кнопки "Поделиться"
}
```

---

## 🎨 HTML СТРУКТУРА РЕЗУЛЬТАТА

```html
<!-- index.html, строки 88-107 -->
<div class="result-card" id="resultCard" style="display: none;">
    
    <!-- Общая сумма (большими цифрами) -->
    <div class="result-total">
        <div class="amount" id="totalAmount">0 ₽</div>
        <div class="label">Общая стоимость</div>
    </div>

    <!-- Детализация расходов -->
    <div id="breakdown">
        <!-- Динамически заполняется в displayResult() -->
        <!-- 
        <div class="breakdown-item">
            <span class="breakdown-label">Цена авто</span>
            <span class="breakdown-amount">925 000 ₽</span>
        </div>
        <div class="breakdown-item">
            <span class="breakdown-label">Пошлины</span>
            <span class="breakdown-amount">185 000 ₽</span>
        </div>
        ... и т.д.
        -->
    </div>

    <!-- Метаданные (возраст, объем, пошлины) -->
    <div class="meta-info" id="metaInfo">
        <!-- Динамически заполняется в displayResult() -->
        <!-- 
        <div>Страна: 🇬🇪 Грузия</div>
        <div>Возраст: 2 лет (от 3 до 5 лет)</div>
        <div>Двигатель: 1500 см³</div>
        ... и т.д.
        -->
    </div>

    <!-- Кнопка "Поделиться" -->
    <button class="share-btn" id="shareBtn" style="display: none;">
        📤 Поделиться результатом
    </button>
</div>
```

---

## 🐛 ПРОБЛЕМЫ, КОТОРЫЕ БЫЛИ ИСПРАВЛЕНЫ

### Проблема 1: `ReferenceError: formatNumber is not defined`

**Причина**: В `displayResult()` вызывалась глобальная функция `formatNumber()`, которая была удалена при переходе на модули в Sprint 6.

**Было**:
```javascript
document.getElementById('totalAmount').textContent = formatNumber(breakdown.total_rub) + ' ₽';
```

**Стало**:
```javascript
document.getElementById('totalAmount').textContent = formatters.formatNumber(breakdown.total_rub) + ' ₽';
```

**Исправлено в строках**: 960, 980, 987, 1009, 1019

---

### Проблема 2: `ReferenceError: getAgeCategory is not defined`

**Причина**: Функция `getAgeCategory()` тоже была перенесена в модуль `formatters.js`, но вызовы не обновились.

**Было**:
```javascript
parts.push(`...${getAgeCategory(meta.age_category)}...`);
```

**Стало**:
```javascript
parts.push(`...${formatters.getAgeCategory(meta.age_category)}...`);
```

**Исправлено в строках**: 1004, 1072

---

## 📝 ПРОВЕРКА ИСПРАВЛЕНИЙ

### Команда для проверки:
```bash
grep -n "formatNumber\|getAgeCategory" app/webapp/index.html | grep -v "formatters\."
```

**Ожидаемый результат**: Пустой вывод (все вызовы используют `formatters.`)

---

## ✅ ИТОГОВАЯ СХЕМА ПОТОКА ДАННЫХ

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER CLICKS "Рассчитать стоимость"                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. calculateCost() - Сбор данных из формы                  │
│    requestData = {country, year, engine_cc, ...}            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. ui.showLoading() - Показываем спиннер                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. api.calculate(requestData) - HTTP POST запрос            │
│    POST http://localhost:8000/api/calculate                 │
│    Body: JSON(requestData)                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. BACKEND - FastAPI обрабатывает запрос                   │
│    /api/calculate → calculate() engine                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. BACKEND RESPONSE - JSON                                  │
│    { breakdown: {...}, meta: {...}, request: {...} }        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. const result = await api.calculate(...)                 │
│    result содержит breakdown, meta, request                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. displayResult(result) - Обработка и отображение         │
│    - Извлекаем breakdown и meta                             │
│    - Форматируем числа через formatters.formatNumber()      │
│    - Форматируем возраст через formatters.getAgeCategory()  │
│    - Создаём DOM элементы                                   │
│    - Вставляем в HTML                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌──��──────────────────────────────────────────────────────────┐
│ 9. ui.showResult() - Показываем карточку результата         │
│    - Анимация fade-in                                       │
│    - Scroll к результату                                    │
│    - Показываем кнопку "Поделиться"                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 10. ui.hideLoading() - Скрываем спиннер                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 11. ✅ РЕЗУЛЬТАТ ПОКАЗАН НА ЭКРАНЕ                         │
│     "1 700 000 ₽" + детализация + метаданные              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 ЛОГИ В КОНСОЛИ (что вы видите)

### Успешный расчет:
```
[calculateCost] Request data: {country: 'georgia', year: 2022, ...}
[APIClient] POST http://localhost:8000/api/calculate {country: 'georgia', ...}
[APIClient] Response 200 OK
[displayResult] Received result: {breakdown: {...}, meta: {...}}
[UI] Showing result card
[UI] Scrolling to result
```

### При ошибке:
```
[calculateCost] Request data: {...}
[APIClient] POST http://localhost:8000/api/calculate
[APIClient] Error: HTTP 500
[APIClient] Error details: {...}
Calculation error: APIError {...}
[UI] Showing error: "Ошибка расчета: ..."
```

---

## 🎯 КЛЮЧЕВЫЕ МОМЕНТЫ

1. **Async/Await**: `await api.calculate()` ждёт ответа от сервера
2. **Деструктуризация**: `const { breakdown, meta } = result` извлекает данные
3. **Модули**: Все функции используют префиксы `formatters.` и `ui.`
4. **Error Handling**: Try-catch ловит ошибки API
5. **Finally**: Спиннер всегда скрывается, даже при ошибке

---

**Всё работает корректно после всех исправлений!** ✅

