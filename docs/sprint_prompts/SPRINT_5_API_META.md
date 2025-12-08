# ПРОМПТ: СПРИНТ 5 — API метаданные и endpoints

## 🎭 РОЛЬ МОДЕЛИ
Ты — **Backend API Engineer** с экспертизой в FastAPI, RESTful API design и OpenAPI/Swagger спецификациях.

---

## 📘 МЕТОДОЛОГИЯ
Используй **Repository Planning Graph (RPG)** — прочти `docs/rpg_intro.txt`.

**Ключевые принципы для этого спринта:**
1. **Стабильные интерфейсы** — новые поля в /api/meta не ломают старых клиентов
2. **Топологический порядок** — сначала routes.py, затем валидация через Swagger
3. **Модульность** — изменения только в routes.py, без затрагивания engine.py

---

## 📊 ГРАФ ПРОЕКТА
**Обязательно обнови** после завершения спринта: `docs/rpg.yaml`

**Добавь в recent_changes:**
```yaml
- date: "2025-12-08"
  description: "SPRINT 5 завершён: Обновлён GET /api/meta (добавлены constraints для engine_power_hp: min=1, max=1500, conversion_factors: hp_to_kw=0.7355), Swagger UI актуален, backward compatibility сохранена"
```

---

## 🎯 ЦЕЛЬ СПРИНТА
Обновить API эндпоинт `/api/meta` для поддержки нового поля `engine_power_hp`:
1. Добавить constraints для мощности двигателя
2. Добавить коэффициенты конвертации (л.с. → кВт)
3. Проверить актуальность других метаданных
4. Протестировать через Swagger UI

---

## 📚 ИСТОЧНИКИ ПРАВДЫ

### Первичные источники (читай ОБЯЗАТЕЛЬНО)
1. **План работ**: `docs/REFACTORING_PLAN.md` (Этап 5, задача 5.1)
2. **Модели данных**: `app/calculation/models.py` (CalculationRequest — поле engine_power_hp)
3. **API routes**: `app/api/routes.py` (эндпоинт GET /api/meta)

### Вторичные источники (для контекста)
4. **Константы фронтенда**: `app/webapp/js/config/constants.js` (Constraints — для синхронизации)
5. **API flow документация**: `docs/API_RESULT_FLOW.md`
6. **Граф проекта**: `docs/rpg.yaml`

### Проблема «Lost in the Middle»
⚠️ **Минимизируй контекст**:
- Читай только routes.py (функция `get_meta()`)
- Открывай models.py только для проверки Field constraints
- Не загружай весь engine.py — там нет нужной информации

---

## ✅ КРИТЕРИИ ДОСТИЖЕНИЯ ЦЕЛИ

### Обязательные (Must Have)
- [ ] **Добавлены constraints** — `engine_power_hp_min: 1`, `engine_power_hp_max: 1500` в response /api/meta
- [ ] **Добавлены conversion_factors** — `hp_to_kw: 0.7355` в response /api/meta
- [ ] **Swagger UI актуален** — `/docs` показывает новые поля в примере ответа
- [ ] **API работает** — `curl http://localhost:8000/api/meta` возвращает JSON с новыми полями
- [ ] **Backward compatibility** — старые поля не удалены, старые клиенты не ломаются

### Проверочные (Should Have)
- [ ] **Синхронизация с models.py** — constraints совпадают с Field(gt=0, le=1500)
- [ ] **Документация** — docstring функции get_meta() обновлён
- [ ] **Тест API** — добавлен test case в `tests/functional/test_api.py`

### Дополнительные (Nice to Have)
- [ ] **Версионирование API** — добавлен поле `api_version: "2.0"` в meta
- [ ] **Changelog ссылка** — добавлено `changelog_url` для отслеживания изменений

---

## 🔍 ЗАДАЧИ (в порядке выполнения)

### Задача 5.1: Изучить текущую структуру /api/meta

**Действия:**
1. Прочитай `app/api/routes.py` — функция `get_meta()`
2. Запусти сервер: `python -m app.main` (или `uvicorn app.main:app --reload`)
3. Открой Swagger UI: `http://localhost:8000/docs`
4. Выполни GET /api/meta и изучи текущий response
5. Сохрани текущую структуру для сравнения

**Ожидаемый текущий ответ:**
```json
{
  "countries": [...],
  "freight_types": [...],
  "age_categories": [...],
  "constraints": {
    "year_min": 1990,
    "year_max": 2025,
    "engine_cc_min": 500,
    "engine_cc_max": 10000,
    "purchase_price_min": 1000,
    "purchase_price_max": 100000000
  },
  "currencies_supported": [...]
}
```

**Критерий готовности:** Понята текущая структура, определено место для новых полей

---

### Задача 5.2: Обновить функцию get_meta()

**Файл:** `app/api/routes.py`

**Изменения:**
```python
@router.get("/meta")
def get_meta() -> dict[str, Any]:
    """
    Метаданные для UI: страны, ограничения валидации, коэффициенты конвертации.
    
    NEW in v2.0:
    - constraints.engine_power_hp_min/max для валидации мощности
    - conversion_factors.hp_to_kw для отображения в UI
    """
    settings = get_settings()
    configs = get_configs()
    
    # ...existing code для countries, freight_types, age_categories...
    
    return {
        # ...existing fields...
        "constraints": {
            "year_min": 1990,
            "year_max": datetime.now(UTC).year,
            "engine_cc_min": 500,
            "engine_cc_max": 10000,
            "engine_power_hp_min": 1,        # NEW
            "engine_power_hp_max": 1500,     # NEW
            "purchase_price_min": 1000,
            "purchase_price_max": 100000000
        },
        "conversion_factors": {              # NEW section
            "hp_to_kw": 0.7355,
            "kw_to_hp": 1.35962              # optional: обратная конвертация
        },
        # ...existing fields...
    }
```

**Критерий готовности:** Код компилируется без ошибок

---

### Задача 5.3: Проверить синхронизацию с models.py

**Действия:**
1. Открой `app/calculation/models.py`
2. Найди определение поля `engine_power_hp` в `CalculationRequest`
3. Сравни constraints:
   ```python
   # В models.py:
   engine_power_hp: int = Field(gt=0, le=1500, description="...")
   
   # В routes.py должно быть:
   # "engine_power_hp_min": 1    (gt=0 означает > 0, минимум 1)
   # "engine_power_hp_max": 1500 (le=1500)
   ```
4. Убедись, что значения совпадают

**Критерий готовности:** Constraints синхронизированы Backend ↔ API

---

### Задача 5.4: Тестирование через Swagger UI

**Действия:**
1. Перезапусти сервер (если нужно)
2. Открой `http://localhost:8000/docs`
3. Найди эндпоинт `GET /api/meta`
4. Нажми "Try it out" → "Execute"
5. Проверь response:
   - Есть ли `constraints.engine_power_hp_min`?
   - Есть ли `constraints.engine_power_hp_max`?
   - Есть ли секция `conversion_factors`?
   - Значение `hp_to_kw` равно `0.7355`?

**Критерий готовности:** Swagger показывает новые поля в примере ответа

---

### Задача 5.5: Автоматизированный тест API

**Файл:** `tests/functional/test_api.py`

**Добавь новый тест:**
```python
def test_get_meta_engine_power_constraints(client: TestClient):
    """
    Проверка наличия constraints для engine_power_hp в /api/meta.
    """
    response = client.get("/api/meta")
    assert response.status_code == 200
    
    data = response.json()
    
    # Проверка constraints
    assert "constraints" in data
    constraints = data["constraints"]
    
    # NEW: Проверка engine_power_hp
    assert "engine_power_hp_min" in constraints
    assert "engine_power_hp_max" in constraints
    assert constraints["engine_power_hp_min"] == 1
    assert constraints["engine_power_hp_max"] == 1500
    
    # NEW: Проверка conversion_factors
    assert "conversion_factors" in data
    factors = data["conversion_factors"]
    assert "hp_to_kw" in factors
    assert factors["hp_to_kw"] == 0.7355


def test_get_meta_backward_compatibility(client: TestClient):
    """
    Убедиться, что старые поля не удалены (backward compatibility).
    """
    response = client.get("/api/meta")
    data = response.json()
    
    # Старые обязательные поля должны присутствовать
    assert "countries" in data
    assert "constraints" in data
    assert "currencies_supported" in data
    assert data["constraints"]["engine_cc_min"] == 500
    assert data["constraints"]["engine_cc_max"] == 10000
```

**Критерий готовности:** `pytest tests/functional/test_api.py::test_get_meta_engine_power_constraints -v` проходит

---

### Задача 5.6: Проверить актуальность других метаданных

**Чеклист:**
- [ ] `countries` — есть ли Georgia? (добавлена 2025-12-04)
- [ ] `age_categories` — актуальны ли lt3, 3_5, gt5?
- [ ] `freight_types` — есть ли все типы фрахта?
- [ ] `currencies_supported` — USD, EUR, JPY, KRW, AED, GEL?

**Если что-то устарело** — обнови в той же функции `get_meta()`

**Критерий готовности:** Все метаданные актуальны на 2025-12-08

---

## 🧪 ТЕСТИРОВАНИЕ

### Manual Testing
```bash
# 1. Запуск сервера
python -m app.main

# 2. Проверка через curl
curl http://localhost:8000/api/meta | jq '.constraints'
# Ожидаемый вывод:
# {
#   "year_min": 1990,
#   "year_max": 2025,
#   "engine_cc_min": 500,
#   "engine_cc_max": 10000,
#   "engine_power_hp_min": 1,        ← NEW
#   "engine_power_hp_max": 1500,     ← NEW
#   ...
# }

curl http://localhost:8000/api/meta | jq '.conversion_factors'
# Ожидаемый вывод:
# {
#   "hp_to_kw": 0.7355,
#   "kw_to_hp": 1.35962
# }

# 3. Автоматизированные тесты
pytest tests/functional/test_api.py::test_get_meta_engine_power_constraints -v
pytest tests/functional/test_api.py::test_get_meta_backward_compatibility -v
```

### Expected Output
```
✅ GET /api/meta возвращает 200 OK
✅ constraints.engine_power_hp_min = 1
✅ constraints.engine_power_hp_max = 1500
✅ conversion_factors.hp_to_kw = 0.7355
✅ Backward compatibility: старые поля присутствуют
✅ Тесты: 2 passed
```

---

## 📝 ДОКУМЕНТАЦИЯ

### Обновление docstring в routes.py
```python
@router.get("/meta")
def get_meta() -> dict[str, Any]:
    """
    Метаданные калькулятора для инициализации UI.
    
    Returns:
        dict: Справочные данные и ограничения валидации
            - countries: список стран с emoji и labels
            - freight_types: типы фрахта
            - age_categories: возрастные категории авто
            - constraints: лимиты полей формы (NEW: engine_power_hp)
            - conversion_factors: коэффициенты конвертации (NEW: hp_to_kw)
            - currencies_supported: поддерживаемые валюты
    
    Changelog:
        - 2025-12-08: Добавлены engine_power_hp constraints и conversion_factors
        - 2025-12-04: Добавлена страна Georgia
    """
    # ...
```

### Обновление rpg.yaml
```yaml
components:
  - name: "get_meta"
    parent_file: "routes.py"
    type: "function"
    description: "GET /api/meta — метаданные калькулятора (страны, constraints для engine_power_hp, conversion_factors: hp_to_kw=0.7355)"
    testable: true
    test_priority: "high"

recent_changes:
  - date: "2025-12-08"
    description: "SPRINT 5 завершён: Обновлён GET /api/meta (engine_power_hp constraints, conversion_factors), добавлены тесты test_get_meta_engine_power_constraints и test_get_meta_backward_compatibility, Swagger UI актуален"
```

---

## 🚨 ПРОБЛЕМЫ И РЕШЕНИЯ

### Проблема: Swagger не показывает новые поля
**Причина:** Кэширование OpenAPI схемы

**Решение:**
1. Перезапусти сервер: `Ctrl+C` → `python -m app.main`
2. Очисти кэш браузера: `Ctrl+Shift+R`
3. Открой Swagger в режиме инкогнито

### Проблема: Тесты падают с KeyError
**Причина:** Старые fixtures не содержат новые поля

**Решение:**
```python
# В tests/conftest.py (если есть mock_meta)
@pytest.fixture
def mock_meta():
    return {
        # ...existing fields...
        "constraints": {
            # ...existing constraints...
            "engine_power_hp_min": 1,
            "engine_power_hp_max": 1500
        },
        "conversion_factors": {
            "hp_to_kw": 0.7355
        }
    }
```

### Проблема: Конфликт версий API
**Решение:** Добавь версионирование (optional)
```python
return {
    "api_version": "2.0",  # NEW: маркер breaking changes
    # ...rest of response...
}
```

---

## ⏱️ ВРЕМЯ ВЫПОЛНЕНИЯ
**Оценка:** 1 час

**Breakdown:**
- Задача 5.1: 10 минут (изучение)
- Задача 5.2: 15 минут (код)
- Задача 5.3: 5 минут (синхронизация)
- Задача 5.4: 10 минут (Swagger проверка)
- Задача 5.5: 15 минут (автотесты)
- Задача 5.6: 5 минут (актуальность метаданных)

---

## 📞 NEXT STEPS
После завершения спринта:
1. **Обнови rpg.yaml** (добавь recent_changes)
2. **Коммит изменений:**
   ```bash
   git add app/api/routes.py tests/functional/test_api.py docs/rpg.yaml
   git commit -m "feat(api): add engine_power_hp constraints and conversion_factors to /api/meta"
   ```
3. **Переходи к Спринту 6** (Фронтенд WebApp) — см. `docs/sprint_prompts/SPRINT_6_FRONTEND_WEBAPP.md`

---

## 🔗 СВЯЗАННЫЕ ФАЙЛЫ
- `docs/REFACTORING_PLAN.md` — полный план (Этап 5)
- `app/api/routes.py` — целевой файл (функция get_meta)
- `app/calculation/models.py` — источник constraints
- `tests/functional/test_api.py` — тесты
- `app/webapp/js/config/constants.js` — фронтенд (синхронизация)

---

**Автор промпта:** RPG Architect  
**Версия:** 1.0  
**Дата:** 2025-12-08

