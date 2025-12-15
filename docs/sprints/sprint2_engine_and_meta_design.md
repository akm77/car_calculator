# Спринт 2: Дизайн применения банковской комиссии в движке и метаданных

## Роль модели

- Модель выступает как **системный архитектор расчётного движка**, который проектирует, но пока не реализует кодовую логику применения банковской комиссии.
- Требуется строго следовать методике **RPG**: чётко описать роли узлов (`engine.py`, `models.py`), процессы (конвертация валюты → RUB с учётом комиссии), границы (что трогаем/не трогаем) и артефакты (структуры в `CalculationMeta`, формат `rates_used`).

## Методика RPG

- **Роли:**
  - Расчётный движок: `app/calculation/engine.py` — место, где будет применяться банковская комиссия.
  - Модели данных/DTO: `app/calculation/models.py` — источник структуры `CalculationMeta` и `CostBreakdown`.
  - Конфиг: `config/commissions.yml` — поставщик процента банковской комиссии.
- **Процессы:**
  - `VALUTA -> RUB` с учётом базового курса CBR и процента `bank_commission`.
  - Заполнение `CalculationMeta` с информацией о базовом курсе и надбавке процента.
- **Границы:**
  - **Изначальный план спринта 2**: не вносить изменений в `.py`‑файлы, ограничиться проектными решениями и документацией.
  - **Фактически к 2025‑12‑15**: дизайн был реализован в коде (см. раздел «Статус реализации» ниже); структура API‑ответа при этом не нарушена — изменения коснулись только внутренних расчётов и метаданных (`meta`).
- **Артефакты:**
  - Описание алгоритма применения банковской комиссии в `docs/SPECIFICATION.md`.
  - Обновлённое RPG‑описание узлов `engine.py` и `models.py` в `docs/rpg.yaml`.

## Источники правды

- `docs/SPECIFICATION.md` — разделы о расчёте стоимости, структуре `CalculationMeta`, `CostBreakdown` и `rates_used`.
- `docs/rpg_intro.txt` — методика RPG, определения ролей и процессов.
- `docs/rpg.yaml` — текущее описание `engine.py`, `models.py`, `config/commissions.yml`.
- `app/calculation/engine.py` — фактический алгоритм расчёта (используется для анализа точек конвертации и структуры итогов).
- `app/calculation/models.py` — актуальная доменная модель (`CalculationRequest`, `CalculationMeta`, `CalculationResult`, `CostBreakdown`).

## Цели спринта

1. **Спроектировать алгоритм применения банковской комиссии в движке**:
   - Определить, что конвертация `amount, currency -> RUB` для реальных платежей использует эффективный курс:
     - `effective_rate = base_rate * (1 + bank_commission_percent/100)`,
     - где `base_rate` — курс от CBR, `bank_commission_percent` — из `config/commissions.yml`.
   - Описать, какие операции считаются «банковскими» (покупка авто, комиссия компании, фрахт, country expenses и т.д.).
2. **Зафиксировать, как банковская комиссия влияет на итог `total_rub`**:
   - `total_rub` в будущей реализации должен включать эффект банковской комиссии за счёт использования эффективных курсов.
   - Не добавлять отдельные поля `bank_commission_*` в breakdown; эффект виден только в `total_rub` и в `rates_used`.
3. **Спроектировать расширение `CalculationMeta` для отражения комиссии**:
   - Добавить в модель (на уровне документации) поле(я) для процента банковской комиссии и связи с базовым курсом:
     - пример: `bank_commission_percent`,
     - формат `rates_used`: `USD/RUB = 78.95 + 1%` при ненулевой комиссии, `USD/RUB = 78.95` при нулевой.
4. **Обновить RPG‑описание узлов движка и моделей**:
   - В `docs/rpg.yaml` зафиксировать:
     - какие функции/части `engine.py` относятся к банковским операциям,
     - как они используют конфиг `bank_commission`,
     - как наполняется `CalculationMeta` новыми данными.

## Критерии достижения целей

1. В `docs/SPECIFICATION.md` есть формальное описание алгоритма применения банковской комиссии:
   - Чётко описан расчёт эффективного курса и правило использования его для всех релевантных конвертаций `VALUTA -> RUB`.
   - Определён перечень операций (стоимость авто, расходы по стране, фрахт, комиссия компании, пошлина — при наличии валютной операции), на которые распространяется комиссия.
2. В SPEC задокументировано поведение итогов:
   - `total_rub` включает банковскую комиссию.
   - Отдельные суммы банковской комиссии **не выводятся** в API, в breakdown и UI.
3. В SPEC и/или отдельном разделе описан формат `CalculationMeta`:
   - Добавлено поле для процента банковской комиссии.
   - Объяснён формат строки для отображения курса: `BASE_RATE + PERCENT%` при ненулевой комиссии и без `+ PERCENT%` при нуле.
4. В `docs/rpg.yaml` обновлены узлы:
   - Для `engine.py` — перечень функций/блоков, использующих банковскую комиссию.
   - Для `models.py` — поля, отражающие банковскую комиссию в `CalculationMeta`.
5. По итогам спринта команда понимает **где именно в коде** будет добавляться логика комиссии, не открывая сам код на изменение.

---

## Статус реализации к 2025‑12‑15

По состоянию на 15 декабря 2025 года цели спринта 2 не только спроектированы, но и реализованы в коде и спецификации.

### Движок (`app/calculation/engine.py`)

- Реализованы функции:
  - `_get_bank_commission_percent(commissions_conf)`: извлекает эффективный процент банковской комиссии из `config.commissions` с учётом `enabled`, `percent` и `meta.default_percent`.
  - `_effective_currency_rate(rates_conf, code, bank_commission_percent)`: считает `effective_rate = base_rate × (1 + bank_commission_percent/100)`.
  - Обновлённый `_convert(amount, currency, rates_conf, bank_commission_percent=None)`: поддерживает конвертацию по базовому или эффективному курсу.
- Банковская комиссия фактически применяется к операциям:
  - конвертация цены покупки (`purchase_price_rub`),
  - расходы по стране (`country_expenses_rub`),
  - фрахт (`freight_rub`),
  - **комиссия компании** (1000 USD и переопределения по странам) — при конвертации в RUB используется `effective_rate`.
- API и структура `CostBreakdown` не изменились: эффект комиссии отражён только в числах (`total_rub`, компоненты в RUB), без добавления новых полей в JSON.

### Модели (`app/calculation/models.py`)

- Добавлен класс `RateUsage`:
  - `base_rate: float`,
  - `effective_rate: float`,
  - `bank_commission_percent: float`,
  - `display: str` (формат типа `"USD/RUB = 78.95 + 1%"`).
- `CalculationMeta` расширен:
  - сохранено старое поле `rates_used: dict[str, float]` (для обратной совместимости),
  - добавлено новое поле `detailed_rates_used: dict[str, RateUsage]` — детализированная информация по использованным валютам.

### Спецификация (`docs/SPECIFICATION.md`)

- Раздел **4.5. «Банковская комиссия (надбавка к валютному курсу)**:
  - описывает структуру `bank_commission` в `config/commissions.yml` и поведение по умолчанию;
  - фиксирует формулу `effective_rate = base_rate × (1 + bank_commission_percent/100)`;
  - перечисляет точки применения комиссии, включая комиссию компании при конвертации 1000 USD в RUB;
  - описывает формат метаданных `CalculationMeta.rates_used`/`detailed_rates_used` (base, percent, effective, display).

### RPG‑описание (`docs/rpg.yaml`)

- Узлы, связанные с банковской комиссией, обновлены:
  - `config_data/commissions.yml` — содержит артефакт `bank_commission`;
  - `app_calculation_engine` — описаны функции и блоки, использующие банковскую комиссию при конвертации валют;
  - `CalculationMeta` — указано, что в `rates_used`/`detailed_rates_used` должны храниться `base_rate`, `bank_commission_percent`, `effective_rate` и человеко‑читаемое представление для UI.
- В `metadata.recent_changes` и `planned_improvements` зафиксирован прогресс по ветке `bank_commission_runtime_support`.

### Тесты

- Добавлены юнит‑тесты (`tests/unit/test_bank_commission.py`), покрывающие:
  - `_get_bank_commission_percent` (отсутствие секции, `enabled: false`, использование `meta.default_percent`, неверные значения);
  - `_effective_currency_rate` для сценариев с 0% и ненулевой комиссией, включая чувствительность к регистру кода валюты.
- Существующие функциональные тесты движка продолжают проверять целостный расчёт, включая влияние банковской комиссии через изменённые RUB‑значения и метаданные.

> Таким образом, спринт 2 можно считать **завершённым не только на уровне дизайна, но и на уровне кода и спецификации**; документ остаётся источником правды о замысле, а приведённый статус помогает сопоставить его с текущей реализацией.

---

## Выбранная архитектура применения bank_commission и effective_rate

### Варианты и фактический выбор

- Рассматривались два архитектурных варианта:
  - **Вариант A**: считать `effective_rate` уже в `app/services/cbr.get_effective_rates()`, т.е. модифицировать конфигурацию курсов (перемножать статический+live курс на фактор `(1 + p/100)` ещё до попадания в движок).
  - **Вариант B**: считать `effective_rate` внутри движка (`app/calculation/engine.py`) в момент конверсии, используя чистые (`base`) курсы из `rates_conf` и глобальный `bank_commission_percent` из `commissions_conf`.
- Фактическая реализованная архитектура — **Вариант B**:
  - `get_effective_rates(base_rates_conf)` в `app/services/cbr.py` **не знает** о `bank_commission` и только сливает статические и live‑курсы, формируя `rates_conf["currencies"]["<CODE>_RUB"]` как **base‑курсы**.
  - Вся логика банковской комиссии сосредоточена в `app/calculation/engine.py`:
    - `_get_bank_commission_percent(commissions_conf) -> float` — извлекает глобальный процент комиссии из `config/commissions.yml::bank_commission` с учётом `enabled`, `percent`, `meta.default_percent` и безопасных фолбэков (отсутствие секции, некорректные типы → 0.0).
    - `_currency_rate(rates_conf, code) -> Decimal` — возвращает **базовый** курс `VALUTA/RUB` (`<CODE>_RUB`) без учёта комиссии.
    - `_effective_currency_rate(rates_conf, code, bank_commission_percent) -> Decimal` — считает `effective_rate = base_rate * (1 + bank_commission_percent / 100)` с защитой на `p=0` (возвращает base как есть).
    - `_convert(amount, currency, rates_conf, bank_commission_percent=None) -> Decimal` — единая точка конверсии `VALUTA -> RUB`:
      - если `bank_commission_percent is None` → используется чистый `base_rate` (режим полной обратной совместимости со старым движком);
      - иначе → используется `_effective_currency_rate(...)`, т.е. `effective_rate` с учётом текущего `bank_commission_percent`.
    - `_convert_from_rub(amount_rub, currency, rates_conf) -> Decimal` — обратная конверсия `RUB -> VALUTA` **всегда по base‑курсу** (используется только для внутренних технических расчётов и нормализации, не отражает отдельный банковский платёж).

### Карта валютных операций в calculate()

В `calculate(req: CalculationRequest)` валютные операции делятся на две группы:

1. **Реальные валютные платежи пользователя (через effective_rate):**
   - **Покупка автомобиля (`purchase_price_rub`)**:
     - `purchase_price_rub = _convert(req.purchase_price, req.currency, rates_conf, bank_commission_percent)`.
     - Если входная валюта не RUB — всегда используется `effective_rate` при включённой комиссии.
   - **Расходы в стране покупки (`country_expenses_rub`)**:
     - Япония:
       - Внутренняя нормализация: `purchase_price_rub -> purchase_price_jpy` через `_convert_from_rub(..., "JPY", rates_conf)` **по base‑курсу** (без комиссии).
       - Выбор тира по `purchase_price_jpy` даёт `expenses_val` в JPY.
       - Конвертация в RUB: `_convert(expenses_val, "JPY", rates_conf, bank_commission_percent)` → через `effective_rate`.
     - Прочие страны:
       - `_other_country_expenses(fees_conf)` возвращает сумму в `expenses_currency` (обычно USD).
       - Конвертация в RUB: `_convert(expenses_val, expenses_currency, rates_conf, bank_commission_percent)`.
   - **Фрахт (`freight_rub_dec`)**:
     - `_select_freight(fees_conf, req.freight_type)` выбирает `amount` и `currency` (обычно USD).
     - `_convert(freight_val, freight_currency, rates_conf, bank_commission_percent)` — всегда через `effective_rate` при `bank_commission_percent > 0`.
   - **Комиссия компании (`_commission`)**:
     - Для структуры вида `by_country.*.commission_usd` и `default_commission_usd`:
       - `_commission(..., rates_conf=rates_conf, bank_commission_percent=bank_commission_percent)` вызывает `_convert(commission_usd, "USD", rates_conf, bank_commission_percent)`.
       - Таким образом, фиксированная комиссия компании (1000 USD и переопределения по странам) конвертируется в RUB по `effective_rate`.
     - Для legacy‑структуры, где комиссия уже задана в RUB (список с `amount`), валютной конверсии нет и комиссия банка не применяется (RUB→RUB операции вне банка).

2. **Технические/административные перерасчёты (всегда по base‑курсу):**
   - **Нормализация японской цены для tier‑ов**:
     - `purchase_price_jpy = _convert_from_rub(purchase_price_rub, "JPY", rates_conf)`.
     - Здесь важен только базовый курс для выбора правильного диапазона в таблице расходов; это не отдельная банковская операция.
   - **Таможенная пошлина (`_compute_duty`)**:
     - Внутри: `eur_rub = _currency_rate(rates_conf, "EUR")` — всегда `base_rate` без комиссии.
     - Для авто `<3 лет` таможенная стоимость в EUR считается как `purchase_price_rub / eur_rub` (при этом `purchase_price_rub` уже содержит эффект банковской комиссии, если она включена).
     - Итоговая пошлина в RUB: `duty_rub = duty_eur * eur_rub` — использование EUR_RUB здесь отражает нормативные правила расчёта, а не новую банковскую транзакцию.
   - **Утильсбор (`_utilization_fee_v2`)**:
     - Считается полностью в RUB по тарифной таблице `utilization_m1_personal` без какой‑либо валютной конверсии.

### Формат данных для курсов и CalculationMeta

- `get_effective_rates(configs.rates)` возвращает словарь `rates_conf`, где:
  - `rates_conf["currencies"]["<CODE>_RUB"]` — **базовый** курс (static + опционально live‑CBR), без учёта `bank_commission`.
  - Дополнительные поля `live_source`, `live_codes` описывают только источник данных.
- Внутри движка:
  - `_currency_rate` использует `rates_conf["currencies"]` как источник **base_rate**.
  - `_effective_currency_rate` умножает `base_rate` на `(1 + bank_commission_percent/100)` и возвращает `effective_rate` (c quantize4).
  - Никакого кеширования `effective_rate` в `rates_conf` не происходит; он считается на лету в `_convert`.
- Метаданные `CalculationMeta` (описаны в `docs/SPECIFICATION.md` и `models.py`) расширены:
  - `rates_used: dict[str, float]` — минимальный контракт для клиентов; сюда кладутся числовые курсы (в текущей реализации — эффективные значения, чтобы `total_rub` и видимый курс были согласованы).
  - `detailed_rates_used: dict[str, RateUsage]` — расширенное описание по каждому использованному коду валюты (`USD`, `EUR`, `JPY`, ...):
    - `base_rate: float` — базовый курс без комиссии;
    - `effective_rate: float` — курс с учётом `bank_commission_percent`;
    - `bank_commission_percent: float` — применённый процент надбавки;
    - `display: str` — человеко‑читаемая строка формата `"USD/RUB = 78.95 + 1%"` или `"USD/RUB = 78.95"` (если комиссия фактически 0).

---

## Инварианты и монотонность total_rub по bank_commission

### Конфигурационные инварианты

- Если секция `bank_commission` в `commissions.yml` **отсутствует** или не является словарём:
  - `_get_bank_commission_percent` возвращает `0.0`.
  - `_effective_currency_rate` при таком `p` эквивалентен `base_rate`.
  - Все конверсии через `_convert(..., bank_commission_percent)` дают те же результаты, что и старый код без комиссии.
- Если `bank_commission.enabled` явно `false`:
  - `_get_bank_commission_percent` также возвращает `0.0` независимо от `percent` и `meta.default_percent`.
- Если `enabled` не задано или `true`, но `percent` не задано:
  - `_get_bank_commission_percent` использует `meta.default_percent` (если он корректно приводится к float), иначе `0.0`.
- Любые некорректные значения (`percent: "abc"`, `meta.default_percent: null` и т.п.) безопасно приводятся к `0.0`.

Таким образом, при отсутствии или явном выключении `bank_commission` **поведение движка полностью совпадает с историческим**: все курсы считаются базовыми, `total_rub` и breakdown идентичны прежним расчётам.

### Монотонность total_rub по bank_commission_percent

- Для всех компонент, конвертируемых через `_convert(..., bank_commission_percent)` с `amount >= 0` и `base_rate >= 0`:
  - `effective_rate(p) = base_rate * (1 + p/100)` — неубывающая функция по `p` при `p >= 0`.
  - Соответственно, `amount * effective_rate(p)` не убывает при увеличении `p`.
- Эти компоненты включают:
  - `purchase_price_rub` (если исходная валюта не RUB),
  - `country_expenses_rub`,
  - `freight_rub`,
  - валютную часть комиссии компании (1000 USD и per‑country `commission_usd`).
- Компоненты, которые не зависят напрямую от `effective_rate` (утильсбор, услуги в РФ, часть пошлины, зависящая только от рублёвых норм и уже конвертированных величин), являются либо константами, либо неубывающими функциями тех же аргументов.

**Бизнес‑инвариант:**

> При фиксированном входном запросе `CalculationRequest` и неизменных конфигурациях `rates.yml`, `fees.yml`, `duties.yml` значение `total_rub` не должно уменьшаться при увеличении `bank_commission_percent`.

Формально, если рассмотреть одну и ту же заявку с четырьмя конфигурациями комиссий:

- A: `bank_commission` отсутствует или `enabled=false`,
- B: `enabled=true, percent=0`,
- C: `enabled=true, percent=1.0`,
- D: `enabled=true, percent=2.0`,

то должны выполняться соотношения:

- `total_rub(A) == total_rub(B)` (строгая обратная совместимость при 0%),
- `total_rub(B) <= total_rub(C) <= total_rub(D)`.

Этот инвариант покрывается отдельными юнит‑тестами в `tests/unit/test_bank_commission.py` и может использоваться как критерий регрессии при изменении логики конверсии.

---

## Резюме для следующих спринтов

- Выбран вариант **B**: `effective_rate` считается внутри `engine.py` при конверсии, а `get_effective_rates` отдаёт только base‑курсы (static+live).
- Все реальные валютные платежи пользователя (покупка авто, расходы по стране, фрахт, комиссия компании в USD) конвертируются в RUB через `_convert(..., bank_commission_percent)` → `effective_rate`.
- Внутренние техпроцессы (RUB↔EUR в пошлине, RUB→JPY для японских тиров) используют только `base_rate` без комиссии.
- Расширенные метаданные `CalculationMeta.detailed_rates_used` содержат `base_rate`, `effective_rate`, `bank_commission_percent` и удобочитаемое поле `display` для UI/бота.
- Гарантирована обратная совместимость при `enabled=false`/отсутствии секции и монотонность `total_rub` по `bank_commission_percent` при прочих равных.
