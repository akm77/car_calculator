# Руководство по миграции на v2.0

**Дата релиза:** 2025-12-08  
**Версия:** 2.0.0  
**Breaking Changes:** ДА (обязательное поле engine_power_hp)

---

## 🎯 Что нового в v2.0

### 1. Новая система утилизационного сбора
- **2D-таблица** (объём двигателя + мощность в кВт)
- **Обязательное поле:** `engine_power_hp` (1-1500 л.с.)
- **Базовая ставка:** 20,000 руб. × коэффициент из таблицы

### 2. Единая фиксированная комиссия
- **1000 USD** для всех стран (было: градация по порогам)
- **Исключение:** ОАЭ = 0 USD

### 3. Обновлённые тарифы 2025
- ЭРА-ГЛОНАСС: 45,000 руб.
- Пошлины lt3: новые брэкеты (325k-6500k RUB)

---

## 🚨 Breaking Changes

### API Endpoints

#### POST /api/calculate

**БЫЛО (v1.x):**
```json
{
  "country": "japan",
  "year": 2022,
  "engine_cc": 1500,
  "purchase_price": 2500000,
  "currency": "JPY"
}
```

**СТАЛО (v2.0):**
```json
{
  "country": "japan",
  "year": 2022,
  "engine_cc": 1500,
  "engine_power_hp": 110,
  "purchase_price": 2500000,
  "currency": "JPY"
}
```

**Ошибка при отсутствии поля:**
```json
{
  "detail": [
    {
      "loc": ["body", "engine_power_hp"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

#### Response Structure Changes

**Новые поля в `meta`:**
```json
{
  "meta": {
    "engine_power_hp": 110,
    "engine_power_kw": 80.91,
    "utilization_coefficient": 0.26
  }
}
```

**Изменения в `breakdown`:**
- `utilization_fee_rub` — теперь рассчитывается по новой системе (значения изменились)
- `company_commission_rub` — теперь фиксированная ставка 1000 USD
- `era_glonass_rub` — обновлено до 45,000 руб.

---

### Configuration Files

#### config/rates.yml

**Добавлена новая секция:**
```yaml
utilization_m1_personal:
  base_rate_rub: 20000
  volume_bands:
    - volume_range: [0, 1000]
      power_brackets:
        - {power_kw_max: 51.48, coefficient_lt3: 0.17, coefficient_gt3: 0.26}
        # ...80+ записей
```

**Обновлено:**
```yaml
era_glonass_rub: 45000  # было: 0 или старое значение
```

#### config/commissions.yml

**БЫЛО:**
```yaml
thresholds:
  - max_price: 1500000
    amount: 40000
  - max_price: 3000000
    amount: 60000
  # ...
```

**СТАЛО:**
```yaml
default_commission_usd: 1000

by_country:
  uae:
    commission_usd: 0
```

---

## 📋 Чеклист миграции

### Для Backend разработчиков

- [ ] **Обновить код клиента API:**
  - Добавить поле `engine_power_hp` во все запросы к `/api/calculate`
  - Обновить типы (если используется TypeScript/Pydantic)
  
- [ ] **Обработать новые поля в response:**
  - `meta.engine_power_hp`, `meta.engine_power_kw`, `meta.utilization_coefficient`
  
- [ ] **Пересчитать ожидаемые значения в тестах:**
  - Утилизационный сбор изменился (новая таблица)
  - Комиссия изменилась (фиксированная ставка)
  
- [ ] **Обновить конфигурационные файлы:**
  - Добавить `config/rates.yml` (новая секция utilization)
  - Обновить `config/commissions.yml` (новая структура)

### Для Frontend разработчиков

- [ ] **Добавить поле в форму:**
  ```html
  <input type="number" name="enginePowerHp" min="1" max="1500" required>
  ```
  
- [ ] **Обновить валидацию:**
  ```javascript
  if (!enginePowerHp || enginePowerHp < 1 || enginePowerHp > 1500) {
    showError('Введите мощность двигателя (1-1500 л.с.)');
  }
  ```
  
- [ ] **Отобразить новые поля в результате:**
  ```javascript
  Мощность: ${result.meta.engine_power_hp} л.с. (${result.meta.engine_power_kw} кВт)
  Коэффициент утильсбора: ${result.meta.utilization_coefficient}
  ```

### Для DevOps

- [ ] **Бэкап текущих конфигов:**
  ```bash
  cp config/rates.yml config/rates_v1_backup.yml
  cp config/commissions.yml config/commissions_v1_backup.yml
  ```
  
- [ ] **Деплой новых конфигов:**
  ```bash
  # Проверка YAML валидности
  yamllint config/*.yml
  
  # Деплой
  rsync -avz config/ production:/app/config/
  ```
  
- [ ] **Мониторинг после деплоя:**
  - Проверка логов на ошибки валидации
  - Мониторинг response time (должно остаться < 200ms)
  - Проверка метрик: количество 422 ошибок (должно быть 0 после миграции клиентов)

---

## 🔄 Rollback Plan

### Если возникли проблемы:

**1. Быстрый откат конфигов (5 минут):**
```bash
# Восстановить старые конфиги
cp config/rates_v1_backup.yml config/rates.yml
cp config/commissions_v1_backup.yml config/commissions.yml

# Перезапустить сервис
systemctl restart car_calculator
```

**2. Откат кода (10 минут):**
```bash
# Откатить на предыдущий релиз
git revert --no-commit HEAD~20..HEAD
git commit -m "revert: rollback to v1.x due to production issues"
git push origin main

# Деплой
./scripts/deploy.sh
```

**3. Откат базы данных (если использовалась миграция):**
```sql
-- Вернуть engine_power_hp в nullable (если хранили в БД)
ALTER TABLE calculations ALTER COLUMN engine_power_hp DROP NOT NULL;
```

---

## 📊 Примеры миграции

### Python (requests)

**БЫЛО:**
```python
import requests

response = requests.post("https://api.example.com/api/calculate", json={
    "country": "japan",
    "year": 2022,
    "engine_cc": 1500,
    "purchase_price": 2500000,
    "currency": "JPY"
})
```

**СТАЛО:**
```python
import requests

response = requests.post("https://api.example.com/api/calculate", json={
    "country": "japan",
    "year": 2022,
    "engine_cc": 1500,
    "engine_power_hp": 110,  # NEW: добавить
    "purchase_price": 2500000,
    "currency": "JPY"
})

# Обработка новых полей
result = response.json()
print(f"Мощность: {result['meta']['engine_power_hp']} л.с.")
print(f"Коэффициент: {result['meta']['utilization_coefficient']}")
```

### JavaScript (fetch)

**БЫЛО:**
```javascript
const response = await fetch('/api/calculate', {
  method: 'POST',
  body: JSON.stringify({
    country: 'japan',
    year: 2022,
    engine_cc: 1500,
    purchase_price: 2500000,
    currency: 'JPY'
  })
});
```

**СТАЛО:**
```javascript
const response = await fetch('/api/calculate', {
  method: 'POST',
  body: JSON.stringify({
    country: 'japan',
    year: 2022,
    engine_cc: 1500,
    engine_power_hp: 110,  // NEW
    purchase_price: 2500000,
    currency: 'JPY'
  })
});

const result = await response.json();
console.log(`Мощность: ${result.meta.engine_power_hp} л.с.`);
console.log(`Коэффициент: ${result.meta.utilization_coefficient}`);
```

### cURL

**БЫЛО:**
```bash
curl -X POST "https://api.example.com/api/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "country": "japan",
    "year": 2022,
    "engine_cc": 1500,
    "purchase_price": 2500000,
    "currency": "JPY"
  }'
```

**СТАЛО:**
```bash
curl -X POST "https://api.example.com/api/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "country": "japan",
    "year": 2022,
    "engine_cc": 1500,
    "engine_power_hp": 110,
    "purchase_price": 2500000,
    "currency": "JPY"
  }'
```

---

## ❓ FAQ

### Q: Обязательно ли указывать engine_power_hp?
**A:** Да, это обязательное поле с версии 2.0. Без него API вернёт ошибку 422.

### Q: Где взять мощность для старых данных?
**A:** Типичные соотношения:
- 1000-1500 cc → 70-110 л.с.
- 1500-2000 cc → 110-150 л.с.
- 2000-3000 cc → 150-250 л.с.

Или используйте автомобильные справочники (specifications по VIN).

### Q: Изменился ли утилизационный сбор для моего авто?
**A:** Скорее всего, да. Новая система учитывает мощность, поэтому даже при одинаковом объёме сумма может отличаться.

### Q: Можно ли использовать старое API?
**A:** Нет, v1.x API снят с поддержки с 2025-12-08. Все клиенты должны мигрировать на v2.0.

### Q: Какой grace period для миграции?
**A:** Немедленная миграция. Если требуется больше времени, свяжитесь с поддержкой.

### Q: Как конвертируется мощность из л.с. в кВт?
**A:** Используется коэффициент 0.7355: `kW = HP × 0.7355`

### Q: Что если мне нужно пересчитать кВт обратно в л.с.?
**A:** Используйте обратный коэффициент 1.35962: `HP = kW × 1.35962`

---

## 📞 Поддержка

**Вопросы по миграции:**  
- Email: support@example.com
- Telegram: @support_bot
- GitHub Issues: https://github.com/your-repo/issues

**Документация:**  
- API Docs: https://api.example.com/docs
- Changelog: [CHANGELOG.md](../CHANGELOG.md)
- Specification: [SPECIFICATION.md](./SPECIFICATION.md)
- API Result Flow: [API_RESULT_FLOW.md](./API_RESULT_FLOW.md)

---

## 📚 См. также

- [SPECIFICATION.md](./SPECIFICATION.md) — Полная спецификация системы
- [CHANGELOG.md](../CHANGELOG.md) — История изменений
- [API_RESULT_FLOW.md](./API_RESULT_FLOW.md) — Структура API ответов
- [REFACTORING_PLAN.md](./REFACTORING_PLAN.md) — План рефакторинга
- [REFACTORING_PROGRESS.md](./REFACTORING_PROGRESS.md) — Прогресс рефакторинга

---

**Последнее обновление:** 2025-12-08  
**Версия документа:** 1.0

