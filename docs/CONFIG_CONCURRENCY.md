# Config Upload Concurrency Protection

## Проблема Race Condition

### Сценарий конфликта

Если два администратора одновременно загружают один и тот же конфиг (например, `fees.yml`):

```
Time | Admin 1                          | Admin 2
-----|----------------------------------|----------------------------------
T0   | /set_fees                        | 
T1   | Upload fees.yml (v1)             | /set_fees
T2   | Validation starts                | Upload fees.yml (v2)
T3   | Validation OK                    | Validation starts
T4   | Create backup                    | Validation OK
T5   | fees.yml → fees.yml.backup       | Create backup (ПЕРЕЗАПИСЬ!)
T6   | Replace fees.yml with v1         | fees.yml → fees.yml.backup
T7   | Success!                         | Replace fees.yml with v2
T8   |                                  | Success! (v1 ПОТЕРЯНА!)
```

### Последствия

1. **Потеря данных**: Изменения Admin1 полностью теряются
2. **Backup confusion**: Backup может содержать промежуточное состояние
3. **Timestamp collision**: Оба backup могут иметь одинаковый timestamp
4. **Inconsistent state**: Нет гарантии атомарности операции

---

## Решение: asyncio.Lock per Config

### Архитектура

```python
# Глобальный словарь locks (по одному на каждый тип конфига)
_CONFIG_LOCKS: dict[ConfigFile, asyncio.Lock] = {}

def _get_config_lock(config_type: ConfigFile) -> asyncio.Lock:
    """Lazy initialization для Lock конкретного конфига."""
    if config_type not in _CONFIG_LOCKS:
        _CONFIG_LOCKS[config_type] = asyncio.Lock()
    return _CONFIG_LOCKS[config_type]
```

### Workflow с Lock

```
Time | Admin 1                          | Admin 2
-----|----------------------------------|----------------------------------
T0   | /set_fees                        |
T1   | Upload fees.yml (v1)             | /set_fees
T2   | Validation starts (no lock)      | Upload fees.yml (v2)
T3   | Validation OK                    | Validation starts (no lock)
T4   | async with lock: ACQUIRE         | Validation OK
T5   |   Create backup                  | async with lock: WAIT... ⏸️
T6   |   Replace fees.yml with v1       | WAIT... ⏸️
T7   | Lock RELEASED ✅                 | ACQUIRE ✅
T8   |                                  |   Create backup (of v1!)
T9   |                                  |   Replace fees.yml with v2
T10  |                                  | Lock RELEASED ✅
```

### Ключевые особенности

1. **Параллельная валидация**: Скачивание и валидация идут БЕЗ lock
   - Экономия времени: валидация может идти параллельно
   - Lock берется только перед модификацией файловой системы

2. **Per-config locking**: Разные конфиги имеют разные locks
   ```python
   # Эти операции идут ПАРАЛЛЕЛЬНО (нет конфликта)
   Admin1: /set_fees     -> lock[FEES]
   Admin2: /set_rates    -> lock[RATES]
   
   # Эти операции идут ПОСЛЕДОВАТЕЛЬНО (защита от race condition)
   Admin1: /set_fees     -> lock[FEES] acquired
   Admin2: /set_fees     -> lock[FEES] waiting...
   ```

3. **Автоматическое освобождение**: `async with lock` гарантирует release даже при exception

4. **Не blocking UI**: Пользователь видит прогресс:
   ```
   ⏳ Downloading and validating...
   🔒 Acquiring lock and saving...
   ✅ fees.yml updated successfully!
   ```

---

## Альтернативные решения (не выбраны)

### 1. File-based locking (flock)

```python
import fcntl

with open(config_path, 'r+') as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    # modify file
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

**Недостатки**:
- ❌ Не работает на всех файловых системах (NFS, SMB)
- ❌ Сложнее обрабатывать ошибки
- ❌ Нужен открытый file descriptor

### 2. Database-based locking

```python
# Redis: SETNX key value
await redis.set("lock:fees", "1", nx=True, ex=60)
```

**Недостатки**:
- ❌ Требует внешнюю зависимость (Redis/PostgreSQL)
- ❌ Добавляет latency (network roundtrip)
- ❌ Overkill для single-instance бота

### 3. Semaphore вместо Lock

```python
sem = asyncio.Semaphore(1)  # Эквивалентно Lock
async with sem:
    # ...
```

**Недостатки**:
- ❌ Semaphore сложнее (можно случайно установить value > 1)
- ✅ Lock - это явное "exclusive access"

### 4. Queue-based serialization

```python
upload_queue = asyncio.Queue()

async def worker():
    while True:
        task = await upload_queue.get()
        await process_upload(task)
        upload_queue.task_done()
```

**Недостатки**:
- ❌ Сложнее архитектура (отдельный worker task)
- ❌ Нужен graceful shutdown для worker
- ❌ Сложнее обрабатывать errors и feedback

---

## Тестирование Concurrency

### Test Case: Simultaneous Upload

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_concurrent_uploads_same_config():
    """Проверка, что одновременные загрузки одного конфига идут последовательно."""
    
    call_order = []
    
    async def mock_backup(config_type):
        call_order.append(f"backup_{config_type.value}_start")
        await asyncio.sleep(0.1)  # Simulate work
        call_order.append(f"backup_{config_type.value}_end")
        return Path("/tmp/backup.yml")
    
    with patch("app.bot.handlers.config.backup_config_file", side_effect=mock_backup):
        # Запускаем две загрузки одновременно
        task1 = asyncio.create_task(process_config_upload(..., ConfigFile.FEES))
        task2 = asyncio.create_task(process_config_upload(..., ConfigFile.FEES))
        
        await asyncio.gather(task1, task2)
    
    # Проверяем, что backup_end первой операции произошел ДО backup_start второй
    assert call_order.index("backup_fees_end") < call_order.index("backup_fees_start")


@pytest.mark.asyncio
async def test_concurrent_uploads_different_configs():
    """Проверка, что загрузки разных конфигов идут параллельно."""
    
    call_order = []
    
    async def mock_backup(config_type):
        call_order.append(f"backup_{config_type.value}_start")
        await asyncio.sleep(0.1)
        call_order.append(f"backup_{config_type.value}_end")
        return Path(f"/tmp/backup_{config_type.value}.yml")
    
    with patch("app.bot.handlers.config.backup_config_file", side_effect=mock_backup):
        # Запускаем загрузки разных конфигов одновременно
        task1 = asyncio.create_task(process_config_upload(..., ConfigFile.FEES))
        task2 = asyncio.create_task(process_config_upload(..., ConfigFile.RATES))
        
        await asyncio.gather(task1, task2)
    
    # Проверяем, что backup операции перемежаются (параллельны)
    fees_start = call_order.index("backup_fees_start")
    rates_start = call_order.index("backup_rates_start")
    fees_end = call_order.index("backup_fees_end")
    rates_end = call_order.index("backup_rates_end")
    
    # Хотя бы одна операция началась до завершения другой
    assert (fees_start < rates_end and rates_start < fees_end)
```

---

## Performance Considerations

### Latency Analysis

**Без Lock (race condition возможна)**:
```
Admin1: Download (2s) + Validate (0.5s) + Backup (0.1s) + Replace (0.1s) = 2.7s
Admin2: Download (2s) + Validate (0.5s) + Backup (0.1s) + Replace (0.1s) = 2.7s
Total wall time: ~2.7s (параллельно)
```

**С Lock (race condition защищена)**:
```
Admin1: Download (2s) + Validate (0.5s) | Lock { Backup (0.1s) + Replace (0.1s) } = 2.7s
Admin2: Download (2s) + Validate (0.5s) | WAIT + Lock { Backup (0.1s) + Replace (0.1s) } = 2.7s + 0.2s = 2.9s
Total wall time: ~2.9s
```

**Overhead**: +0.2s для второго администратора (только на backup+replace операциях)

### Почему валидация БЕЗ lock?

1. **Валидация read-only**: Не модифицирует файловую систему
2. **Экономия времени**: Валидация может занимать >1s для больших файлов
3. **Fail fast**: Если файл невалидный, второй админ узнает об этом раньше
4. **Меньше blocking**: Lock держится только для critical section (0.2s)

---

## Monitoring & Debugging

### Логи

```python
import structlog

logger = structlog.get_logger()

async with lock:
    logger.info(
        "config_upload_lock_acquired",
        config_type=config_type.value,
        user_id=message.from_user.id,
    )
    # ... backup and replace
    logger.info(
        "config_upload_lock_released",
        config_type=config_type.value,
        duration_ms=(time.time() - start_time) * 1000,
    )
```

### Метрики

```python
from prometheus_client import Histogram

config_upload_duration = Histogram(
    "config_upload_duration_seconds",
    "Time spent uploading config (including lock wait)",
    ["config_type", "stage"],
)

# Использование
with config_upload_duration.labels(config_type="fees", stage="validation").time():
    await download_and_validate_config(...)

with config_upload_duration.labels(config_type="fees", stage="locked_section").time():
    async with lock:
        # backup and replace
```

---

## FAQ

**Q: Почему asyncio.Lock, а не threading.Lock?**  
A: Telegram боты работают в asyncio event loop. threading.Lock блокировал бы весь event loop.

**Q: Что если бот перезапустится во время загрузки?**  
A: Lock существует только в памяти и сбрасывается. Temporary файл останется в /tmp и будет очищен ОС.

**Q: Может ли Lock deadlock?**  
A: Нет, т.к. используется только один Lock за раз и `async with` гарантирует release.

**Q: Что если админ отправит /cancel во время ожидания lock?**  
A: FSM state очистится, но Lock уже waiting. После acquire операция завершится, но пользователь не получит уведомление.

**Q: Нужно ли lock для /get_* команд (download)?**  
A: Нет, чтение файла безопасно во время записи благодаря атомарности shutil.move().

---

## References

- [Python asyncio.Lock Documentation](https://docs.python.org/3/library/asyncio-sync.html#asyncio.Lock)
- [aiogram FSM Storage Keys](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/storages.html)
- [Race Condition Prevention Patterns](https://en.wikipedia.org/wiki/Race_condition#Prevention)

