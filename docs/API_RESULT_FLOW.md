# 📖 ПОДРОБНОЕ ОБЪЯСНЕНИЕ: Как получаем результат расчета от API

**Дата**: 8 декабря 2025 (обновлено для v2.0)  
**Файл**: `app/webapp/index.html`  
**API Endpoint**: `POST /api/calculate`

> **⚠️ ВАЖНО (v2.0):** С версии 2.0.0 добавлено **обязательное поле** `engine_power_hp` (1-1500 л.с.)  
> См. [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) для деталей миграции.  
> **⚠️ ВАЖНО (bank_commission, sprint 3):** Формат JSON-ответа `/api/calculate` **не меняется**, но
> семантика поля `breakdown.total_rub` уточняется: итоговая сумма **уже включает эффект банковской
> комиссии**, так как все части, зависящие от валютного курса, рассчитываются по эффективному курсу
> `effective_rate = base_rate × (1 + bank_commission_percent/100)` (см. раздел 4.5 в `SPECIFICATION.md`).

---

## 🔗 Обзор потока данных (движок → API → WebApp / бот)

```text
[User]
  │  вводит параметры в WebApp или Telegram WebApp
  ▼
[WebApp JS]
  │  POST /api/calculate (JSON-запрос)
  ▼
[FastAPI /api/calculate]
  │  валидирует запрос → вызывает engine.calculate()
  ▼
[Calculation Engine]
  │  считает CostBreakdown (в RUB)
  │  формирует CalculationMeta (включая rates_used и detailed_rates_used)
  ▼
[CalculationResult]
  │  сериализуется в JSON (breakdown, meta, request)
  ▼
[WebApp / Bot]
  │  показывают breakdown.total_rub и детали
  └▶ используют meta.rates_used (и detailed_rates_used) для отображения строки курса
      вида: "USD/RUB = BASE_RATE [+ PERCENT%]" без раскрытия суммы комиссии
```

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
    "purchase_price_rub": 925000.0,
    "duties_rub": 185000.0,
    "utilization_fee_rub": 340000.0,
    "customs_services_rub": 5000.0,
    "era_glonass_rub": 25000.0,
    "freight_rub": 150000.0,
    "country_expenses_rub": 50000.0,
    "company_commission_rub": 20000.0,
    "total_rub": 1700000.0
  },
  "meta": {
    "age_years": 2,
    "age_category": "3_5",
    "volume_band": "1500-2000",
    "engine_power_hp": 110,
    "engine_power_kw": 80.91,
    "utilization_coefficient": 0.26,
    "customs_value_eur": 9500.0,
    "duty_formula_mode": "percent",
    "duty_percent": 0.2,
    "duty_min_rate_eur_per_cc": 0.5,
    "vehicle_type": "M1",
    "warnings": [],
    "rates_used": {
      "USD_RUB": 78.95,
      "EUR_RUB": 85.10
    },
    "detailed_rates_used": {
      "USD": {
        "base_rate": 78.95,
        "effective_rate": 79.7395,
        "bank_commission_percent": 1.0,
        "display": "USD/RUB = 78.95 + 1%"
      },
      "EUR": {
        "base_rate": 85.10,
        "effective_rate": 85.951,
        "bank_commission_percent": 1.0,
        "display": "EUR/RUB = 85.10 + 1%"
      }
    }
  },
  "request": {
    "country": "georgia",
    "year": 2022,
    "engine_cc": 1500,
    "engine_power_hp": 110,
    "purchase_price": 10000.0,
    "currency": "USD",
    "freight_type": "open",
    "vehicle_type": "M1"
  }
}
```

> **Важно про `total_rub` и банковскую комиссию:**  
> * Структура объекта `breakdown` **не меняется** — новые поля
>   вида `bank_commission_percent`, `bank_commission_rub` в JSON **не добавляются**.  
> * Поля `purchase_price_rub`, `freight_rub`, `country_expenses_rub`,
>   `company_commission_rub` и другие компоненты, зависящие от валюты, внутри движка
>   рассчитываются по **эффективному курсу** `effective_rate`, в который уже
>   «вшита» банковская комиссия (`base_rate × (1 + percent/100)`).  
> * Соответственно, `breakdown.total_rub` — это сумма этих компонент **уже с учётом
>   банковской комиссии**. Клиенты API не видят комиссию как отдельную сумму.

---

### 6️⃣ Функция `displayResult(result)` - отображение результата в WebApp

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

## 💱 Как WebApp отображает курс и банковскую комиссию

На уровне API и движка банковская комиссия применяется через эффективный курс валюты
(`effective_rate`), а не отдельным числовым полем. Клиентам (WebApp, Telegram‑бот) нужна только
подсказка, **какой курс был использован** и есть ли к нему надбавка.

### Источник данных

- Источником правды о курсах для UI служит `CalculationMeta.rates_used` (и/или
  связанное поле, описанное в `docs/SPECIFICATION.md`, раздел 4.5.4).  
- Для каждой пары вида `USD_RUB`, `JPY_RUB` сервер формирует **строковое
  представление**, достаточное для показа пользователю.

Пример логического содержимого (не меняет официальный JSON-контракт ответа, показывает идею):

```json
{
  "meta": {
    "rates_used": {
      "USD_RUB": {
        "display": "USD/RUB = 78.95 + 1%"
      }
    }
  }
}
```

### Правило форматирования строки курса в WebApp

WebApp **не вычисляет** курс и комиссию самостоятельно — он только
использует подготовленную сервером информацию.

- При ненулевой банковской комиссии (`bank_commission_percent > 0` в движке):  
  **UI‑строка:** `USD/RUB = BASE_RATE + PERCENT%`  
  Пример: `USD/RUB = 78.95 + 1%`
- При комиссии 0% или отключённом блоке `bank_commission`:  
  **UI‑строка:** `USD/RUB = BASE_RATE`  
  Пример: `USD/RUB = 78.95`

Где именно показывается строка в WebApp:

- Строка с курсом выводится в блоке метаданных `metaInfo` (под общей суммой и
  детализацией) отдельной строкой, например:
  - `Курс: USD/RUB = 78.95 + 1%`
- WebApp получает эту строку из `meta.rates_used` и вставляет её как есть, без
  пересчётов и доступа к внутренним полям `base_rate` или `effective_rate`.

### Что пользователь **не может** делать в WebApp

- В форме ввода **нет** полей и переключателей, связанных с банковской
  комиссией: нельзя задать процент, включить/выключить комиссию или редактировать её.  
- Вся логика и значение комиссии управляются только конфигурацией сервера
  (`config/commissions.yml::bank_commission`).
- В `breakdown` **нет** строки «Банковская комиссия XXX ₽» — эффект комиссии
  виден только
  - в увеличившихся рублёвых суммах (`purchase_price_rub`, `freight_rub`, …),
  - в строке курса вида `USD/RUB = 78.95 + 1%`.

---

## 🤖 Как Telegram‑бот отображает курс и банковскую комиссию

Telegram‑бот использует те же данные, что и WebApp, но формирует
текстовый ответ в чате.

### Источник данных

- Хендлеры бота (`app/bot/handlers/start.py`) получают объект
  `CalculationResult` из движка.  
- Для целей отображения курса бот опирается на ту же
  информацию, что и WebApp — `meta.rates_used` (внутренне это может быть
  либо готовая строка, либо набор полей для её сборки).  
- В сообщениях пользователю бот **не показывает** отдельную сумму
  банковской комиссии, только курс и рублёвые итоги.

### Формат строки курса в ответе бота

Рекомендуемый формат (аналогичен WebApp):

- При комиссии > 0%:

  ```text
  Курс: USD/RUB = 78.95 + 1%
  ```

- При комиссии = 0% или отключённой:

  ```text
  Курс: USD/RUB = 78.95
  ```

Эта строка выводится в верхней части сообщения с результатом (после блока о
стране/годе/двигателе, до детализации расходов), например:

```text
💰 Расчёт стоимости растаможки

🇯🇵 Страна: Япония
📅 Год: 2021 (3_5)
⚙️ Объём: 1496 см³
🔋 Мощность: 110 л.с. (80.91 кВт)
Курс: USD/RUB = 78.95 + 1%

📊 Детализация:
• Стоимость покупки (в рублях): ...
...
💎 ИТОГО: 1 700 000 ₽
```

### Ограничения интерфейса ��ота

- Бот **не добавляет** новых команд для работы с банковской комиссией.  
- В чате **нет** дополнительных полей ввода, связанных с комиссией.  
- Настройки комиссии полностью задаются конфигурацией сервера, бот лишь
  отражает надбавку к курсу через текст `+ X%`.

---

## 🧠 Краткое резюме для клиентов API

- Формат JSON‑ответа `/api/calculate` **стабилен**: поля объекта `breakdown`
  и `meta` остаются прежними.  
- Банковская комиссия **не имеет собственных полей** в JSON — она
  учитывается только через:
  - эффективные курсы, по которым считаются рублёвые суммы,  
  - строковое представление курса в `meta.rates_used` вида
    `BASE_RATE [+ PERCENT%]`.
- WebApp и Telegram‑бот:
  - используют `meta.rates_used` для отображения курса;  
  - показывают надбавку только в виде `+ X%` рядом с курсом;  
  - не предоставляют пользователю возможности управлять размером комиссии.
