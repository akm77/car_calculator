# Спринт 1: Конфиг и метаданные банковской комиссии

## Роль модели

Ты выступаешь как **архитектор и разработчик бэкенда**, отвечающий за дизайн конфигурации банковской комиссии и её интеграцию в доменную модель **без изменения существующей реализации кода**.

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
  - рабочий конфиг `config/commissions.yml` (мы только описываем, как должна выглядеть секция `bank_commission`).

## Цели спринта

1. **Спроектировать и формально описать конфиг банковской комиссии** в `config/commissions.yml`:
   - определить структуру секции `bank_commission` (ключи, типы, семантика);
   - задать поведение по умолчанию и рекомендуемый диапазон значений (0–10%).
2. **Зафиксировать связь конфига с движком и метаданными**:
   - описать в `docs/SPECIFICATION.md`, как банковская комиссия влияет на `total_rub` и `CalculationMeta.rates_used`;
   - зафиксировать формулу `effective_rate = base_rate × (1 + bank_commission_percent/100)`.
3. **Обновить документацию под RPG-подход**:
   - обновить `docs/rpg.yaml` для узлов `config_data`, `engine.py`, `CalculationMeta`;
   - добавить запись в `metadata.recent_changes` про SPRINT 1 и `planned_improvements` для будущей реализации bank_commission в коде.

## Ограничения спринта

- Все изменения **ограничены документацией** и, при необходимости, **примером YAML**.
- **Не вносить** изменений в:
  - реальные конфиги `config/commissions.yml`, `config/rates.yml`, `config/duties.yml`, `config/fees.yml`;
  - любые `.py`-файлы (`app/calculation/engine.py`, `app/calculation/models.py` и др.).
- Банковская комиссия **не пересчитывается в коде**, только описывается:
  - где будет жить в конфиге;
  - как должна влиять на расчёты и метаданные;
  - как это отразится в будущем в API и UI.

## Проектирование конфига `bank_commission`

Логическое место хранения — файл `config/commissions.yml`, новая секция `bank_commission`.

### Структура секции (концептуальная)

Рекомендуемая структура (пример YAML, **не боевой конфиг**):

```yaml
bank_commission:
  enabled: true            # опционально; если false или отсутствует, комиссия считается 0%
  percent: 2.0             # глобальная надбавка к курсу, в процентах

  meta:
    recommended_min: 0.0   # рекомендованный минимум
    recommended_max: 10.0  # рекомендованный максимум (мягкое ограничение)
    warn_above: 10.0       # порог, выше которого конфиг в будущем должен помечаться warning'ом
    default_percent: 0.0   # значение по умолчанию, если percent не задан

  # Возможное будущее расширение (в этом спринте только фиксируем как опцию дизайна):
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
  - `>10%` — допустимо, но в будущем должна быть валидация с:
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
   - дополнен описанием, что кроме фиксированной комиссии компании (1000 USD, исключения по странам) существует **специфицированная секция `bank_commission`**:
     - `enabled`, `percent` (рекомендуемый диапазон 0–10%);
     - `meta.recommended_min/max`, `warn_above`, `default_percent`;
     - возможное будущее расширение `by_component`.

3. **Узел `CalculationMeta` (в `models.py`)**:
   - описание расширено указанием, что в будущем поле `rates_used` должно хранить для каждой валюты:
     - `base_rate`;
     - `bank_commission_percent`;
     - `effective_rate`;
   - это нужно для отображения в UI курса вида `USD/RUB = BASE_RATE + X%`.

4. **Связи (edges)**:
   - между `config_data` → `app_calculation` добавлено описание, что:
     - в будущих спринтах `engine.calculate` будет использовать `bank_commission.percent` при расчёте `effective_rate`;
     - `CalculationMeta.rates_used` будет хранить `base_rate/bank_commission_percent/effective_rate`.

5. **planned_improvements**:
   - добавлен элемент `bank_commission_runtime_support` с этапами:
     - дизайн алгоритма в `engine.py` (SPRINT 2);
     - расширение `CalculationMeta.rates_used` и API/клиентов (SPRINT 3);
     - реализация чтения `bank_commission`, применение `effective_rate` и тесты (SPRINT 4).

## Разграничение комиссий

Важно явно различать два вида комиссий (это отражено и в SPEC, и в RPG):

- **Комиссия компании**:
  - уже реализована в v2.0;
  - фиксированная сумма в USD (по умолчанию 1000 USD, исключение для ОАЭ);
  - задаётся в `config/commissions.yml` (`default_commission_usd`, `by_country.*.commission_usd`).

- **Банковская комиссия**:
  - в этом спринте **только специфицируется** как `bank_commission.percent` в `commissions.yml`;
  - реализуется как надбавка к курсу валюты `base_rate` → `effective_rate`;
  - влияет на `total_rub` и `meta.rates_used`, но не выделяется как отдельная сумма в breakdown.

## Критерии достижения целей

1. **SPECIFICATION.md**:
   - есть отдельный подпункт «Банковская комиссия (надбавка к валютному курсу)», в котором:
     - описана структура `bank_commission` (ключи, поведение по умолчанию);
     - зафиксирована формула `effective_rate = base_rate × (1 + bank_commission_percent/100)`;
     - описано влияние на `total_rub` и `CalculationMeta.rates_used`;
     - разведены термины «комиссия компании» и «банковская комиссия».

2. **docs/rpg.yaml**:
   - в `metadata.recent_changes` есть запись о добавлении спецификации `bank_commission` (SPRINT 1);
   - узел `config_data` / `commissions.yml` описывает артефакт `bank_commission` и его параметры;
   - узел `CalculationMeta` содержит указание на будущую структуру `rates_used` (base_rate, bank_commission_percent, effective_rate);
   - в межмодульных связях отражено, что `bank_commission` в будущем пойдёт по цепочке `config → engine → meta → UI`;
   - в `planned_improvements` есть пункт про реализацию bank_commission в коде.

3. **Этот документ (`sprint1_bank_commission_config.md`)**:
   - содержит:
     - цели спринта и ограничения;
     - описанную структуру `bank_commission` с примером YAML;
     - связь с движком и метаданными (SPEC);
     - перечень изменений в `docs/rpg.yaml`;
     - чёткие критерии готовности.

4. **Код и боевые конфиги**:
   - никакие `.py`-файлы не были изменены в рамках спринта;
   - `config/commissions.yml` **не содержит** новой секции `bank_commission` (она описана только как спецификация).

## Как проверить спринт руками

1. Открыть `docs/SPECIFICATION.md` и убедиться, что:
   - существует подпункт про банковскую комиссию;
   - в нём явно указаны:
     - структура `bank_commission` (enabled, percent, meta.*);
     - формула `effective_rate`;
     - правила по умолчанию (отсутствие секции/значения = 0%);
     - диапазон 0–10% и поведение при >10%.

2. Открыть `docs/rpg.yaml` и проверить, что:
   - в `metadata.recent_changes` есть запись о SPRINT 1 и `bank_commission`;
   - в узле `config_data` / `commissions.yml` описан артефакт `bank_commission`;
   - в описании `CalculationMeta` зафиксирован будущий формат `rates_used`;
   - в `planned_improvements` есть элемент `bank_commission_runtime_support`.

3. Открыть этот файл (`docs/sprints/sprint1_bank_commission_config.md`) и убедиться, что:
   - он содержит цели, ограничения, структуру `bank_commission`, пример YAML и критерии готовности;
   - явно указано, что код и боевые конфиги не меняются.

4. Проверить через `git diff`, что в рамках спринта затронуты только:
   - `docs/SPECIFICATION.md`;
   - `docs/rpg.yaml`;
   - `docs/sprints/sprint1_bank_commission_config.md`.
