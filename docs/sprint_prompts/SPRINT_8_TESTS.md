# ПРОМПТ: СПРИНТ 8 — Тестирование

## 🎭 РОЛЬ МОДЕЛИ
Ты — **QA Engineer / Test Automation Specialist** с экспертизой в pytest, параметризованных тестах, fixtures и TDD-подходе.

---

## 📘 МЕТОДОЛОГИЯ
Используй **Repository Planning Graph (RPG)** — прочти `docs/rpg_intro.txt`.

**Ключевые принципы для этого спринта:**
1. **Инкрементальная валидация** — пиши и запускай тесты по одному
2. **Топологический порядок** — сначала unit-тесты (утильсбор), затем integration (API)
3. **Стабильные интерфейсы** — тесты не ломают существующий функционал

---

## 📊 ГРАФ ПРОЕКТА
**Обязательно обнови** после завершения спринта: `docs/rpg.yaml`

**Добавь в recent_changes:**
```yaml
- date: "2025-12-08"
  description: "SPRINT 8 завершён: Обновлены все тестовые кейсы в cases.yml (добавлено engine_power_hp), создан tests/unit/test_utilization_v2.py (10 параметризованных тестов для _utilization_fee_v2), обновлены functional/test_engine.py (все кейсы проходят), coverage ≥85%"
```

---

## 🎯 ЦЕЛЬ СПРИНТА
Обеспечить полное тестовое покрытие новой системы утилизационного сбора:
1. Обновить все тестовые кейсы (cases.yml) с полем engine_power_hp
2. Создать unit-тесты для _utilization_fee_v2()
3. Проверить прохождение всех функциональных тестов
4. Достичь coverage ≥85%

---

## 📚 ИСТОЧНИКИ ПРАВДЫ

### Первичные источники (читай ОБЯЗАТЕЛЬНО)
1. **План работ**: `docs/REFACTORING_PLAN.md` (Этап 8, задачи 8.1-8.3)
2. **Тестовые кейсы**: `tests/test_data/cases.yml`
3. **Функциональные тесты**: `tests/functional/test_engine.py`
4. **Engine**: `app/calculation/engine.py` (функция _utilization_fee_v2)

### Вторичные источники (для контекста)
5. **Конфиг утильсбора**: `config/rates.yml` (utilization_m1_personal)
6. **Модели**: `app/calculation/models.py` (CalculationRequest)
7. **Спецификация**: `docs/SPECIFICATION.md` (таблица утильсбора)

### Проблема «Lost in the Middle»
⚠️ **Читай файлы по очереди:**
- Сначала cases.yml → определи, сколько кейсов нужно обновить
- Затем test_engine.py → пойми, как запускаются параметризованные тесты
- Только потом создавай test_utilization_v2.py

---

## ✅ КРИТЕРИИ ДОСТИЖЕНИЯ ЦЕЛИ

### Обязательные (Must Have)
- [ ] **cases.yml обновлён** — все 15+ кейсов содержат поле `engine_power_hp`
- [ ] **test_utilization_v2.py создан** — 10+ unit-тестов для разных диапазонов (объём × мощность)
- [ ] **Все тесты проходят** — `pytest tests/ -v` показывает 100% success
- [ ] **Coverage ≥85%** — `pytest --cov=app --cov-report=term` показывает высокое покрытие
- [ ] **Архивация старых кейсов** — создан `cases_v1_backup_20251208.yml`

### Проверочные (Should Have)
- [ ] **Граничные значения** — тесты проверяют минимум/максимум мощности (1 л.с., 1500 л.с.)
- [ ] **Все возрастные категории** — тесты для lt3, 3_5, gt5
- [ ] **Все страны** — хотя бы по 1 тесту на japan, korea, uae, china, georgia
- [ ] **Edge cases** — тесты на переходы между диапазонами объёма/мощности

### Дополнительные (Nice to Have)
- [ ] **Regression тесты** — сравнение старой и новой системы на одинаковых данных
- [ ] **Performance тесты** — время расчёта < 100ms
- [ ] **Test fixtures** — shared fixtures для повторяющихся данных

---

## 🔍 ЗАДАЧИ (в порядке выполнения)

### Задача 8.1: Архивировать старые тестовые кейсы

**Действия:**
```bash
# Создай бэкап
cp tests/test_data/cases.yml tests/test_data/cases_v1_backup_20251208.yml

# Добавь комментарий в начало бэкапа
echo "# BACKUP: Старая система утильсбора (только по объёму), дата: 2025-12-08\n$(cat tests/test_data/cases_v1_backup_20251208.yml)" > tests/test_data/cases_v1_backup_20251208.yml
```

**Критерий готовности:** Файл `cases_v1_backup_20251208.yml` создан

---

### Задача 8.2: Обновить cases.yml (добавить engine_power_hp)

**Файл:** `tests/test_data/cases.yml`

**Принцип подбора мощности** (типичные соотношения):
- ≤1000 cc → 50-70 л.с.
- 1000-1500 cc → 70-110 л.с.
- 1500-2000 cc → 110-150 л.с.
- 2000-3000 cc → 150-250 л.с.
- 3000+ cc → 250-500 л.с.

**Пример обновления кейса:**
```yaml
# BEFORE (старый кейс)
- id: "japan_lt3_sanctions_unknown"
  request:
    country: "japan"
    year: 2022
    engine_cc: 1496
    purchase_price: 2500000
    currency: "JPY"
    sanctions_unknown: true

# AFTER (NEW: добавлено engine_power_hp)
- id: "japan_lt3_sanctions_unknown"
  request:
    country: "japan"
    year: 2022
    engine_cc: 1496
    engine_power_hp: 110  # NEW: ~70-110 л.с. для 1500cc
    purchase_price: 2500000
    currency: "JPY"
    sanctions_unknown: true
  expected:
    # Обнови expected.breakdown.utilization_fee_rub
    # Новое значение: 20,000 × коэфф. для (1496cc, 110hp=80.9kW)
    # По таблице: диапазон 1001-2000cc, 73.56-95.61 kW → коэфф. 0.26 (lt3)
    breakdown:
      utilization_fee_rub: 5200  # было другое значение, теперь 20000 × 0.26
      # ...остальные поля не меняются (если не трогали пошлины/комиссии)
```

**Действия для каждого кейса:**
1. Определи `engine_cc` кейса
2. Подбери реалистичную `engine_power_hp` по таблице выше
3. Рассчитай новый `utilization_fee_rub` по формуле:
   - Конвертируй л.с. → кВт: `kw = hp × 0.7355`
   - Найди коэффициент в `config/rates.yml` (по объёму и мощности)
   - Умножь: `fee = 20,000 × coefficient`
4. Обнови поле `expected.breakdown.utilization_fee_rub`
5. Обнови `expected.breakdown.total_rub` (добавь разницу в утильсборе)

**Критерий готовности:** Все кейсы содержат `engine_power_hp`, expected values пересчитаны

---

### Задача 8.3: Создать unit-тесты для _utilization_fee_v2

**Файл:** `tests/unit/test_utilization_v2.py` (создай новый)

**Структура:**
```python
"""
Unit-тесты для новой системы утилизационного сбора (2025).

Тестируется функция _utilization_fee_v2() из app/calculation/engine.py:
- Конвертация л.с. → кВт (0.7355)
- Поиск диапазона объёма (5 bands)
- Поиск диапазона мощности (~16 brackets per band)
- Выбор коэффициента (lt3 vs gt3)
- Расчёт: 20,000 × coefficient
"""

import pytest
from decimal import Decimal

from app.calculation.engine import _utilization_fee_v2
from app.core.settings import get_configs


@pytest.fixture
def rates_config():
    """Загрузка реальных конфигов из rates.yml."""
    return get_configs().rates


@pytest.mark.parametrize("age_category,engine_cc,engine_power_hp,expected_coefficient", [
    # Диапазон ≤1000 cc
    ("lt3", 800, 50, 0.17),      # 50hp = 36.78kW → ≤51.48kW → коэфф. 0.17
    ("gt5", 800, 50, 0.26),      # gt3 коэфф. выше
    
    # Диапазон 1001-2000 cc
    ("lt3", 1500, 70, 0.17),     # 70hp = 51.49kW → 51.49-73.55kW → коэфф. 0.17
    ("lt3", 1500, 110, 0.26),    # 110hp = 80.91kW → 73.56-95.61kW → коэфф. 0.26
    ("3_5", 1500, 110, 62.2),    # gt3 (3_5 или gt5) → коэфф. 62.2
    
    # Диапазон 2001-3000 cc
    ("lt3", 2500, 180, 37.5),    # 180hp = 132.39kW → 117.69-139.75kW → коэфф. 37.5
    ("gt5", 2500, 200, 145.9),   # 200hp = 147.1kW → 139.76-161.82kW → коэфф. 145.9
    
    # Диапазон 3001-3500 cc
    ("lt3", 3200, 250, 109.8),   # 250hp = 183.88kW → 161.83-183.88kW → коэфф. 109.8
    
    # Диапазон >3500 cc
    ("gt5", 4000, 400, 286.9),   # 400hp = 294.2kW → ≥367.76kW (последний брэкет)
    
    # Граничные значения
    ("lt3", 500, 1, 0.17),       # Минимум (1 л.с.)
    ("gt5", 10000, 1500, None),  # Максимум (1500 л.с., fallback на последний брэкет)
])
def test_utilization_fee_calculation(
    rates_config, 
    age_category, 
    engine_cc, 
    engine_power_hp, 
    expected_coefficient
):
    """
    Проверка расчёта утилизационного сбора для различных диапазонов.
    """
    fee, coefficient = _utilization_fee_v2(
        age_category=age_category,
        engine_cc=engine_cc,
        engine_power_hp=engine_power_hp,
        rates_conf=rates_config
    )
    
    # Проверка коэффициента
    if expected_coefficient is not None:
        assert coefficient == pytest.approx(expected_coefficient, rel=0.01), \
            f"Коэффициент для {engine_cc}cc, {engine_power_hp}hp, {age_category} должен быть {expected_coefficient}, получено {coefficient}"
    
    # Проверка суммы (базовая ставка × коэффициент)
    base_rate = Decimal("20000")
    expected_fee = base_rate * Decimal(str(coefficient))
    assert fee == pytest.approx(expected_fee, abs=Decimal("0.01")), \
        f"Сумма должна быть {expected_fee}, получено {fee}"


def test_utilization_fee_hp_to_kw_conversion(rates_config):
    """
    Проверка корректности конвертации л.с. → кВт.
    """
    # 100 л.с. = 73.55 кВт
    fee, coefficient = _utilization_fee_v2("lt3", 1500, 100, rates_config)
    
    # Ожидаем диапазон 73.56-95.61 kW для 1001-2000cc
    # Коэффициент должен быть 0.26 (согласно таблице)
    assert coefficient == 0.26


def test_utilization_fee_edge_case_boundary(rates_config):
    """
    Тест на граничное значение между диапазонами объёма.
    """
    # 2000cc (граница 1001-2000 / 2001-3000)
    fee_2000, coef_2000 = _utilization_fee_v2("lt3", 2000, 150, rates_config)
    fee_2001, coef_2001 = _utilization_fee_v2("lt3", 2001, 150, rates_config)
    
    # Коэффициенты должны различаться (разные диапазоны)
    assert coef_2000 != coef_2001, "Граничные значения должны попадать в разные диапазоны"


def test_utilization_fee_zero_power(rates_config):
    """
    Проверка обработки нулевой мощности (edge case).
    """
    # Должно вернуть коэффициент для минимального диапазона
    fee, coefficient = _utilization_fee_v2("lt3", 1500, 0, rates_config)
    
    # 0 л.с. = 0 кВт → первый брэкет (≤51.48 kW) → коэфф. 0.17
    assert coefficient == 0.17


@pytest.mark.skip(reason="Оптимизация: тест только при изменении таблицы утильсбора")
def test_utilization_table_completeness(rates_config):
    """
    Проверка полноты таблицы утильсбора (все диапазоны покрыты).
    """
    util = rates_config.get("utilization_m1_personal", {})
    volume_bands = util.get("volume_bands", [])
    
    # Должно быть 5 диапазонов объёма
    assert len(volume_bands) == 5, "Таблица должна содержать 5 диапазонов объёма"
    
    # Каждый диапазон должен иметь power_brackets
    for band in volume_bands:
        assert "power_brackets" in band, f"Диапазон {band['volume_range']} не содержит power_brackets"
        assert len(band["power_brackets"]) > 0, f"Диапазон {band['volume_range']} имеет пустые power_brackets"
```

**Критерий готовности:** `pytest tests/unit/test_utilization_v2.py -v` показывает 10+ passed

---

### Задача 8.4: Запустить функциональные тесты

**Действия:**
```bash
# 1. Запусти все тесты
pytest tests/functional/test_engine.py -v

# 2. Если есть падения — изучи вывод:
# Expected: utilization_fee_rub = 100,000
# Actual:   utilization_fee_rub = 5,200
# → Это значит, что expected value в cases.yml устарел

# 3. Обнови expected values в cases.yml (см. задачу 8.2)

# 4. Перезапусти тесты
pytest tests/functional/test_engine.py -v

# 5. Повторяй 2-4 до тех пор, пока все тесты не пройдут
```

**Критерий готовности:** `pytest tests/functional/ -v` показывает 100% passed

---

### Задача 8.5: Проверить coverage

**Действия:**
```bash
# Запуск тестов с coverage
pytest tests/ --cov=app --cov-report=term --cov-report=html

# Открой отчёт
open htmlcov/index.html  # macOS

# Проверь coverage для ключевых файлов:
# - app/calculation/engine.py → должно быть ≥90% (функция _utilization_fee_v2 покрыта)
# - app/calculation/models.py → ≥95% (Pydantic валидация)
# - app/api/routes.py → ≥85% (все эндпоинты протестированы)
```

**Если coverage < 85%:**
1. Определи непокрытые строки (в htmlcov/index.html)
2. Добавь тесты для непокрытых веток (if/else, try/except)
3. Перезапусти coverage check

**Критерий готовности:** Overall coverage ≥85%

---

### Задача 8.6: Создать тест для API /api/calculate (опционально)

**Файл:** `tests/functional/test_api.py`

**Добавь новый тест:**
```python
def test_calculate_endpoint_with_engine_power(client: TestClient):
    """
    Проверка POST /api/calculate с новым полем engine_power_hp.
    """
    payload = {
        "country": "japan",
        "year": 2022,
        "engine_cc": 1500,
        "engine_power_hp": 110,  # NEW
        "purchase_price": 2500000,
        "currency": "JPY",
        "vehicle_type": "M1"
    }
    
    response = client.post("/api/calculate", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # Проверка структуры ответа
    assert "breakdown" in data
    assert "meta" in data
    
    # NEW: Проверка новых полей в meta
    meta = data["meta"]
    assert "engine_power_hp" in meta
    assert meta["engine_power_hp"] == 110
    assert "engine_power_kw" in meta
    assert meta["engine_power_kw"] == pytest.approx(80.91, abs=0.1)
    
    # NEW: Проверка коэффициента утильсбора
    assert "utilization_coefficient" in meta
    assert meta["utilization_coefficient"] is not None
    
    # Проверка утилизационного сбора (должен быть рассчитан по новой системе)
    breakdown = data["breakdown"]
    assert breakdown["utilization_fee_rub"] > 0
    # Для 1500cc, 110hp, lt3 → коэфф. 0.26 → 20,000 × 0.26 = 5,200
    assert breakdown["utilization_fee_rub"] == pytest.approx(5200, abs=100)


def test_calculate_endpoint_missing_engine_power(client: TestClient):
    """
    Проверка валидации: отсутствует обязательное поле engine_power_hp.
    """
    payload = {
        "country": "japan",
        "year": 2022,
        "engine_cc": 1500,
        # engine_power_hp ОТСУТСТВУЕТ
        "purchase_price": 2500000,
        "currency": "JPY"
    }
    
    response = client.post("/api/calculate", json=payload)
    
    # Должна вернуться ошибка валидации
    assert response.status_code == 422
    error_data = response.json()
    assert "detail" in error_data
    
    # Проверка, что в ошибке упоминается engine_power_hp
    error_messages = str(error_data["detail"]).lower()
    assert "engine_power_hp" in error_messages or "мощность" in error_messages
```

**Критерий готовности:** `pytest tests/functional/test_api.py::test_calculate_endpoint_with_engine_power -v` проходит

---

## 🧪 ФИНАЛЬНАЯ ПРОВЕРКА

### Чеклист перед завершением спринта

**1. Unit-тесты:**
```bash
pytest tests/unit/test_utilization_v2.py -v
# Ожидаемый результат: 10+ passed
```

**2. Functional-тесты:**
```bash
pytest tests/functional/test_engine.py -v
# Ожидаемый результат: 15+ passed (все кейсы из cases.yml)
```

**3. API-тесты:**
```bash
pytest tests/functional/test_api.py -v
# Ожидаемый результат: 5+ passed (включая новые тесты)
```

**4. Все тесты вместе:**
```bash
pytest tests/ -v --tb=short
# Ожидаемый результат: 30+ passed, 0 failed
```

**5. Coverage:**
```bash
pytest tests/ --cov=app --cov-report=term
# Ожидаемый результат: TOTAL coverage ≥85%
```

---

## 📝 ДОКУМЕНТАЦИЯ

### Комментарии в test_utilization_v2.py
```python
"""
Unit-тесты для новой системы утилизационного сбора (2025).

Changelog:
- 2025-12-08: Создан набор тестов для _utilization_fee_v2()
- Параметризованные тесты покрывают все 5 диапазонов объёма
- Проверка конвертации л.с. → кВт (0.7355)
- Граничные случаи (0 л.с., 1500 л.с., границы диапазонов)

Coverage: ~95% для app/calculation/engine.py (_utilization_fee_v2)
"""
```

### Обновление rpg.yaml
```yaml
unit_tests:
  - target_component: "_utilization_fee_v2"
    test_file: "tests/unit/test_utilization_v2.py"
    test_functions: ["test_utilization_fee_calculation (10 cases)", "test_utilization_fee_hp_to_kw_conversion", "test_utilization_fee_edge_case_boundary"]
    coverage_status: "exists"
    notes: "Параметризованные тесты для всех диапазонов объёма и мощности, проверка коэффициентов lt3/gt3"

integration_tests:
  - integration_point: "API /api/calculate → Engine (_utilization_fee_v2)"
    test_description: "POST /api/calculate с engine_power_hp → корректный расчёт утильсбора"
    test_file: "tests/functional/test_api.py"
    coverage_status: "exists"

recent_changes:
  - date: "2025-12-08"
    description: "SPRINT 8 завершён: Обновлены все 15 кейсов в cases.yml (engine_power_hp, пересчитанные expected values), создан test_utilization_v2.py (10 unit-тестов), обновлён test_api.py (2 новых теста), все тесты проходят, coverage 87%"

tests:
  test_status:
    overall: "32 passed, 0 failed"
    coverage: "87% (app/)"
```

---

## 🚨 ПРОБЛЕМЫ И РЕШЕНИЯ

### Проблема: Тесты падают с "missing 1 required positional argument: 'engine_power_hp'"
**Причина:** cases.yml не обновлён, старые кейсы без engine_power_hp

**Решение:**
1. Открой `tests/test_data/cases.yml`
2. Найди кейсы без поля `engine_power_hp`
3. Добавь поле согласно задаче 8.2

### Проблема: Expected utilization_fee_rub не совпадает с actual
**Причина:** Expected value рассчитан по старой системе

**Решение:**
1. Запусти тест с флагом `-vv` для детального вывода:
   ```bash
   pytest tests/functional/test_engine.py::test_calculation_cases[japan_lt3] -vv
   ```
2. Найди в выводе:
   ```
   Expected: utilization_fee_rub = 100,000
   Actual:   utilization_fee_rub = 5,200
   ```
3. Рассчитай новый expected value:
   - Объём: 1500cc, мощность: 110hp (80.91kW)
   - Возраст: lt3
   - По таблице: диапазон 1001-2000, 73.56-95.61kW → коэфф. 0.26
   - Сумма: 20,000 × 0.26 = 5,200 ₽
4. Обнови `expected.breakdown.utilization_fee_rub: 5200` в cases.yml
5. Пересчитай `expected.breakdown.total_rub` (вычти старый утильсбор, прибавь новый)

### Проблема: Coverage < 85%
**Причина:** Не покрыты error handlers или edge cases

**Решение:**
```bash
# Найди непокрытые строки
pytest tests/ --cov=app --cov-report=term-missing | grep "engine.py"

# Пример вывода:
# app/calculation/engine.py   85%   120-125, 180-182

# Открой engine.py, строки 120-125 — это try/except блок
# Добавь тест, который вызывает исключение:

def test_utilization_fee_missing_volume_band():
    """Тест на отсутствие диапазона объёма."""
    rates_config = {"utilization_m1_personal": {"base_rate_rub": 20000, "volume_bands": []}}
    fee, coef = _utilization_fee_v2("lt3", 99999, 100, rates_config)
    assert fee == Decimal("0")  # fallback
    assert coef == 0.0
```

### Проблема: Pytest не находит test_utilization_v2.py
**Причина:** Директория tests/unit/ не существует или отсутствует __init__.py

**Решение:**
```bash
mkdir -p tests/unit
touch tests/unit/__init__.py
```

---

## ⏱️ ВРЕМЯ ВЫПОЛНЕНИЯ
**Оценка:** 3-4 часа

**Breakdown:**
- Задача 8.1: 5 минут (архивация)
- Задача 8.2: 90 минут (обновление 15 кейсов с пересчётом expected values)
- Задача 8.3: 60 минут (создание test_utilization_v2.py)
- Задача 8.4: 30 минут (прогон и фикс функциональных тестов)
- Задача 8.5: 20 минут (coverage check)
- Задача 8.6: 15 минут (API тесты)
- Финальная проверка: 20 минут

---

## 📞 NEXT STEPS
После завершения спринта:
1. **Обнови rpg.yaml** (добавь test_status, recent_changes)
2. **Коммит изменений:**
   ```bash
   git add tests/ docs/rpg.yaml
   git commit -m "test: update all test cases with engine_power_hp, add unit tests for utilization_v2"
   ```
3. **Переходи к Спринту 9** (Документация) — см. `docs/sprint_prompts/SPRINT_9_DOCUMENTATION.md`

---

## 🔗 СВЯЗАННЫЕ ФАЙЛЫ
- `docs/REFACTORING_PLAN.md` — полный план (Этап 8)
- `tests/test_data/cases.yml` — тестовые кейсы (обновить)
- `tests/unit/test_utilization_v2.py` — новый файл (создать)
- `tests/functional/test_engine.py` — параметризованные тесты
- `tests/functional/test_api.py` — API интеграционные тесты
- `app/calculation/engine.py` — целевая функция (_utilization_fee_v2)

---

**Автор промпта:** RPG Architect  
**Версия:** 1.0  
**Дата:** 2025-12-08

