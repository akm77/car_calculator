# Config Management via Telegram

## Overview

Telegram бот предоставляет полный набор команд для управления конфигурационными файлами без доступа к серверу. Поддерживаются 4 типа конфигов:

- **fees.yml** — тарифы стран и фрахта
- **commissions.yml** — комиссии (включая bank_commission)
- **rates.yml** — курсы валют и утильсбор
- **duties.yml** — таблицы пошлин

---

## Commands

### Download Commands

```
/get_fees          — Скачать fees.yml
/get_commissions   — Скачать commissions.yml
/get_rates         — Скачать rates.yml
/get_duties        — Скачать duties.yml
/list_configs      — Список всех конфигов со статусом (✅/❌)
```

**Features**:
- Отправка файла как Telegram document с caption
- Caption содержит: описание файла и размер
- 404 handling: если файл не найден, выдается понятное сообщение

---

### Upload Commands (FSM-based)

```
/set_fees          — Загрузить новый fees.yml
/set_commissions   — Загрузить новый commissions.yml
/set_rates         — Загрузить новый rates.yml
/set_duties        — Загрузить новый duties.yml
/cancel            — Отменить текущую загрузку
```

**Upload Workflow**:

1. Admin sends `/set_fees` command
2. Bot enters FSM state `waiting_for_fees`
3. Bot sends message: "📤 Upload new fees.yml"
4. Admin uploads `fees.yml` file
5. Bot validates:
   - ✅ Filename matches `fees.yml` (защита от path traversal)
   - ✅ Size ≤ 1MB
   - ✅ Valid YAML syntax (yaml.safe_load)
   - ✅ Required keys present: `countries`, `freight`
6. Bot acquires Lock (wait if another upload in progress)
7. Bot creates backup: `fees.yml.backup.20251228_120000`
8. Bot replaces old file atomically (shutil.move)
9. Bot releases Lock
10. Bot confirms: "✅ fees.yml updated successfully!"
11. Admin uses `/reload_configs` to apply changes

---

## Security & Validation

### 4-Level Validation

1. **Filename Validation**
   - Must match expected filename exactly (`fees.yml`, not `../../../etc/passwd.yml`)
   - Prevents path traversal attacks

2. **Size Validation**
   - Max file size: **1 MB**
   - Prevents DOS attacks and accidental large uploads

3. **YAML Syntax Validation**
   - Uses `yaml.safe_load()` (no code execution)
   - Catches malformed YAML before saving

4. **Structure Validation**
   - Checks for required top-level keys
   - Example for fees.yml: must have `countries` and `freight`

---

## Race Condition Protection

### Problem

If two admins upload the same config simultaneously:

```
Admin 1: Download → Validate → Backup → Replace (v1)
Admin 2: Download → Validate → Backup → Replace (v2) ← v1 LOST!
```

### Solution: asyncio.Lock per Config

```python
# Each config type has its own Lock
_CONFIG_LOCKS: dict[ConfigFile, asyncio.Lock] = {}

async def process_config_upload(...):
    # 1. Download and validate (WITHOUT lock - parallel)
    temp_path = await download_and_validate_config(...)
    
    # 2-3. Acquire lock (wait if busy)
    lock = _get_config_lock(config_type)
    async with lock:
        backup_config_file(config_type)   # Backup old
        shutil.move(temp_path, target)    # Replace atomically
    # Lock released
```

**Benefits**:
- ✅ Different configs can be uploaded in parallel (separate locks)
- ✅ Same config uploads are serialized (no data loss)
- ✅ Validation is parallel (no lock needed for read-only operations)
- ✅ Lock held only for ~0.2s (backup + replace)

See [CONFIG_CONCURRENCY.md](CONFIG_CONCURRENCY.md) for detailed analysis.

---

## Backup System

### Backup Format

```
fees.yml.backup.20251228_143022
          └─── YYYYMMDD_HHMMSS (UTC)
```

### Backup Behavior

- **Automatic**: Created before every successful upload
- **Timestamp**: UTC time, prevents collisions
- **Metadata preserved**: `shutil.copy2()` preserves modification time
- **No backup on first upload**: If original file doesn't exist

### Restoration

To restore from backup:

```bash
cp config/fees.yml.backup.20251228_143022 config/fees.yml
# Then use /reload_configs in bot
```

---

## Error Handling

### Validation Errors

```
❌ Validation failed:

Filename must be `fees.yml`, got `rates.yml`
```

```
❌ Validation failed:

File too large: 2.50MB (max 1MB)
```

```
❌ Validation failed:

Invalid YAML syntax:
mapping values are not allowed here
  in "<unicode string>", line 3, column 10
```

```
❌ Validation failed:

Missing required keys: freight
```

### Upload Errors

```
❌ Failed to save config:

[Errno 28] No space left on device
```

### FSM Errors

```
❌ Please send a document file.
```

---

## Configuration Registry

After uploading a new config, changes are **NOT applied automatically**. Use `/reload_configs` to reload all configs into runtime.

### ConfigRegistry Integration

```python
from app.core.settings import config_registry

# Reload all configs
config_registry.reload_all()

# Access current config
fees_config = config_registry.get_fees()
```

---

## Testing

### Unit Tests

**test_config_upload.py** (24 tests):
- `validate_yaml_structure()` — 8 tests
- `backup_config_file()` — 3 tests
- Upload start commands — 4 tests
- `/cancel` command — 2 tests
- `download_and_validate_config()` — 5 tests
- Concurrency protection — 5 tests

**Coverage**: ≥ 90%

### Manual Testing

1. Start bot: `python -m app.main`
2. Send `/set_fees` to bot
3. Upload `config/fees.yml`
4. Check backup created: `ls -la config/*.backup.*`
5. Send `/reload_configs`
6. Verify changes applied

---

## Admin Access Control

**⚠️ TODO in CONFIG-04**: Add AdminOnlyMiddleware

Currently, all commands are accessible to all users. In SPRINT CONFIG-04:

- Add `ADMIN_USER_IDS` to `.env`
- Create `AdminOnlyMiddleware`
- Apply to `config_handlers` router
- Add `/whoami` command to get user ID
- Add audit logging

---

## References

- [SPRINT_CONFIG_03_upload_commands.md](../sprints/SPRINT_CONFIG_03_upload_commands.md)
- [CONFIG_CONCURRENCY.md](CONFIG_CONCURRENCY.md) — Race condition analysis
- [aiogram FSM Documentation](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/)
- [Python asyncio.Lock](https://docs.python.org/3/library/asyncio-sync.html#asyncio.Lock)

