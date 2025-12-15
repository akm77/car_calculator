# Спринт 1: Конфиг и метаданные банковской комиссии

## Роль модели

Ты выступаешь как **архитектор и разработчик бэкенда**, отвечающий за дизайн конфигурации банковской комиссии
и её интеграцию в доменную модель **без изменения существующей реализации кода**.

В этом спринте важно:
- чётко развести понятия **«комиссия компании»** и **«банковская комиссия»**;
- зафиксировать, **где и как** живёт банковская комиссия в конфиге;
- описать, **как она влияет** на расчёты и метаданные — на уровне спецификации и RPG-графа.

## Методика RPG

Работа ведётся в стиле **RPG (Repository Planning Graph)**:
- фиксируем **роли**: конфиг, движок, модели, API, UI;
- фиксируем **границы**: что трогаем в этом спринте, а что оставляем неизменным;
- определяем **артефакты**: файлы, структуры данных, схемы и связи между ними.

В этом спринте:
- изменяются **только**:
  - `docs/SPECIFICATION.md` (добавляется подпункт про банковскую комиссию);
  - `docs/rpg.yaml` (обновляется RPG-карта: узлы config_data, engine.py, CalculationMeta, recent_changes, planned_improvements);
  - сам этот документ (`docs/sprints/sprint1_bank_commission_config.md`).
- **не изменяются**:
  - никакие `.py`-файлы;
  - реальные конфиги `config/commissions.yml`, `config/rates.yml`, `config/duties.yml`, `config/fees.yml`.

## Цели спринта

1. **Спроектировать и формально описать конфиг банковской комиссии** в `config/commissions.yml`:
   - определить структуру секции `bank_commission` (ключи, типы, семантика);
   - задать поведение по умолчанию и рекомендуемый диапазон значений (0–10%).
2. **Зафиксировать связь конфига с движком и метаданными**:
   - описать в `docs/SPECIFICATION.md`, как банковская комиссия влияет на `total_rub` и `CalculationMeta.rates_used`;
   - зафиксировать формулу `effective_rate = base_rate × (1 + bank_commission_percent/100)`.
3. **Обновить документацию по RPG-подходу**:
   - обновить `docs/rpg.yaml` для узлов `config_data`, `engine.py`, `CalculationMeta`;
   - добавить запись в `metadata.recent_changes` про SPRINT 1 и `planned_improvements` для будущей реализации
     bank_commission в коде.

## Ограничения спринта

- Все изменения **ограничены документацией** и примером YAML.
- **Не вносить** изменений в:
  - реальные конфиги `config/commissions.yml`, `config/rates.yml`, `config/duties.yml`, `config/fees.yml`;
  - любые `.py`-файлы (`app/calculation/engine.py`, `app/calculation/models.py` и др.).
- Банковская комиссия **не пересчитывается в коде**, только описывается:
  - где будет жить в конфиге;
  - как должна влиять на расчёты и метаданные;
  - как это отразится в будущем в API и UI.

## Проектирование конфига `bank_commission`

Логическое место хранения — файл `config/commissions.yml`, новая секция `bank_commission` рядом с уже
существующей структурой комиссии компании (`default_commission_usd`, `by_country`).

### Структура секции (концептуальная)

Рекомендуемая структура (пример YAML, **не боевой конфиг**, но совпадающая с целевым дизайном):

```yaml
bank_commission:
  enabled: false            # опционально; false или отсутствие секции = 0% комиссии
  percent: 0.0              # глобальная надбавка к курсу, в процентах

  meta:
    recommended_min: 0.0    # рекомендуемый минимум
    recommended_max: 10.0   # рекомендуемый максимум (мягкое ограничение)
    warn_above: 10.0        # порог, выше которого конфиг в будущем помечается warning'ом
    default_percent: 0.0    # значение по умолчанию, если percent не задан

  # Возможное будущее расширение (в этом спринте только фиксируем как дизайн-опцию):
  # by_component:
  #   car_purchase_usd:
  #     percent: 2.0
  #   freight_usd:
  #     percent: 1.0
  #   local_costs_jpy:
  #     percent: 3.5
```

### Правила по умолчанию и диапазоны

- Если секция `bank_commission` **отсутствует** — банковская комиссия = `0%`.
- Если секция есть, но:
  - `enabled: false` — комиссия = `0%` независимо от `percent`;
  - `percent` не задан — используется `meta.default_percent` (если не задан, трактуем как `0%`).
- Рекомендуемый диапазон:
  - `0–10%` — «зелёный» диапазон, без предупреждений;
  - `>10%` — допустимо, но в будущем должно сопровождаться:
    - предупреждением в логах и/или
    - предупреждением в метаданных расчёта.

## Связь с движком и метаданными (SPEC)

В `docs/SPECIFICATION.md` добавлен подпункт **«4.5. Банковская комиссия (надбавка к валютному курсу)»**, который фиксирует контракт:

- Банковская комиссия — **процентная надбавка к курсу** валюты до конвертации в RUB.
- Формула:
  - `effective_rate = base_rate × (1 + bank_commission_percent / 100)`.
- Эффект **не выделяется отдельной строкой** в API/JSON, а проявляется через:
  - изменение `breakdown.total_rub`;
  - структуру `CalculationMeta.rates_used`.
- Для каждой валюты в `rates_used` в будущем должны быть доступны поля:
  - `base_rate`;
  - `bank_commission_percent`;
  - `effective_rate`.
- Поведение по умолчанию:
  - отсутствие `bank_commission` или `percent` ⇒ `bank_commission_percent = 0`;
  - диапазон `0–10%` — рекомендуемый;
  - `>10%` — допустимо, но требует предупреждения.

## Изменения в RPG-карте (`docs/rpg.yaml`)

В `docs/rpg.yaml` зафиксировано следующее:

1. **metadata.recent_changes**:
   - добавлена запись о SPRINT 1:
     - формализована банковская комиссия как надбавка к валютному курсу;
     - описана секция `bank_commission` в `config/commissions.yml`;
     - задан контракт `effective_rate` и связь с `total_rub` и `CalculationMeta.rates_used`;
     - разведены понятия «комиссия компании» и «банковская комиссия».

2. **Узел `config_data` / файл `commissions.yml`**:
   - дополнен описанием, что помимо фиксированной комиссии компании (1000 USD, исключения по странам)
     существует **специфицированная секция `bank_commission`**:
     - `enabled`, `percent` (рекомендуемый диапазон 0–10%);
     - `meta.recommended_min/max`, `warn_above`, `default_percent`;
     - возможное будущее расширение `by_component`.

3. **Узел `CalculationMeta` (в `models.py`)**:
   - описание расширено указанием, что в будущем поле `rates_used` должно хранить для каждой валюты:
     - `base_rate`;
     - `bank_commission_percent`;
     - `effective_rate`;
   - это нужно для отображения в UI курсов вида `USD/RUB = BASE_RATE + X%`.

4. **Связи (edges)**:
   - между `config_data` → `app_calculation` добавлено описание, что:
     - в будущих спринтах `engine.calculate` будет использовать `bank_commission.percent`
       при расчёте `effective_rate`;
     - `CalculationMeta.rates_used` будет хранить `base_rate/bank_commission_percent/effective_rate`.

5. **planned_improvements**:
   - добавлен элемент `bank_commission_runtime_support` со стадиями:
     - дизайн алгоритма применения в `engine.py` (SPRINT 2);
     - расширение `CalculationMeta.rates_used` и описание формата в API/клиентах (SPRINT 3);
     - реализация чтения `bank_commission`, внедрение `effective_rate` в расчёты и тесты (SPRINT 4).

## Разграничение комиссий

Важно явно различать два вида комиссий (это отражено и в SPEC, и в RPG):

- **Комиссия компании**:
  - уже реализована в v2.0;
  - фиксированная сумма в USD (по умолчанию 1000 USD, исключение для ОАЭ);
  - задаётся в `config/commissions.yml` (`default_commission_usd`, `by_country.*.commission_usd`).

- **Банковская комиссия**:
  - в этом спринте **только специфицируется** как `bank_commission.percent` в `commissions.yml`;
  - реализуется как надбавка к курсу валюты `base_rate → effective_rate`;
  - влияет на `total_rub` и `meta.rates_used`, но не выделяется как отдельная сумма в breakdown.

## Тестовые конфиги и дальнейшие шаги (связь со Спринтом 4.1)

В последующих спринтах (в т.ч. SPRINT 4.1) для поддержки новой схемы комиссий и
bank_commission были добавлены тестовые YAML-файлы в `tests/test_data/config/`:

- `commissions_company_only.yml` — конфиг с комиссией компании (`default_commission_usd`,
  `by_country.uae.commission_usd = 0`) без секции `bank_commission`; используется как
  базовый тестовый конфиг, чтобы функциональные тесты не зависели от локальных правок
  `config/commissions.yml`;
- `commissions_with_bank.yml` — пример того же формата, но с включённой секцией
  `bank_commission` (enabled, percent, meta.*), предназначенный для будущих тестов
  сценариев с банковской комиссией.

Фикстура `tests/conftest.py::_ensure_test_commissions_defaults` в рамках миграции
со старой структуры `thresholds` переведена на использование тестового YAML, совместимого
со SPEC и целевым форматом `commissions.yml`. Это позволяет:

- сохранить детерминированность существующих тестов;
- не ломать публичный контракт API;
- постепенно вводить тест-кейсы с включённой `bank_commission`, не затрагивая
  текущие сценарии без комиссии.

## Критерии достижения целей

1. **SPECIFICATION.md**:
   - есть подпункт про банковскую комиссию с:
     - описанной структурой `bank_commission` (ключи, поведение по умолчанию);
     - формулой `effective_rate = base_rate × (1 + bank_commission_percent/100)`;
     - описанием влияния на `total_rub` и `CalculationMeta.rates_used`;
     - разведением терминов «комиссия компании» и «банковская комиссия».

2. **docs/rpg.yaml**:
   - в `metadata.recent_changes` есть запись о SPRINT 1 и `bank_commission`;
   - узел `config_data` / `commissions.yml` описывает артефакт `bank_commission` и его параметры;
   - узел `CalculationMeta` содержит указание на будущий формат `rates_used`;
   - в связях отражено прохождение `bank_commission` по цепочке `config → engine → meta → UI`;
   - в `planned_improvements` есть пункт про реализацию bank_commission в коде.

3. **Этот документ (`sprint1_bank_commission_config.md`)**:
   - содержит цели, ограничения, структуру `bank_commission`, пример YAML и критерии готовности;
   - явно указывает, что код и боевые конфиги не меняются.

4. **Код и боевые конфиги**:
   - `.py`-файлы не были изменены в рамках спринта;
   - `config/commissions.yml` может (в будущих спринтах) получить реальную секцию `bank_commission`,
     но на момент завершения SPRINT 1 она рассматривается как спецификация и целевой формат.
