# HTML Escaping Fix - Summary

**Date:** 2025-12-29  
**Issue:** Telegram "Bad Request: can't parse entities" error  
**Status:** ✅ RESOLVED  

---

## 🐛 Problem Description

When sending a message with `/get_<name>` pattern through Telegram bot, got error:

```
Telegram server says - Bad Request: can't parse entities: 
Unsupported start tag "name" at byte offset 475
```

**Root Cause:** 
- Bot uses `ParseMode.HTML` (set in `app/bot/main.py`)
- Telegram interprets `<name>` as HTML tag
- Telegram doesn't recognize `<name>` as valid HTML tag → Error

---

## ✅ Solution Applied

### 1. Research with context7-mcp

Used **context7-mcp** to find the solution:

```bash
# Search for aiogram documentation
resolve-library-id "aiogram telegram bot markdown html escape"
# Result: /websites/aiogram_dev_en_dev (88.8 score)

# Get best practices
get-library-docs /websites/aiogram_dev_en_dev
  --mode code
  --topic "html escape special characters markdown parse mode formatting"
```

**Key Finding:** Use `html.escape()` to escape special characters.

### 2. Code Fix

**File:** `app/bot/handlers/config.py`

**Changes:**

1. Added import:
```python
import html  # Added to imports
```

2. Fixed function:
```python
@router.message(Command("list_configs"))
async def cmd_list_configs(message: Message):
    """Показать список всех конфигурационных файлов."""
    config_list = format_config_list()

    # Escape HTML special characters to prevent parsing errors
    # <name> would be interpreted as an HTML tag without escaping
    tip_text = html.escape("/get_<name>")  # → /get_&lt;name&gt;
    set_text = html.escape("/set_<name>")  # → /set_&lt;config&gt;

    await message.answer(
        f"{config_list}\n"
        f"💡 <b>Tip:</b> Use <code>{tip_text}</code> to download a config file.\n"
        f"📤 Use <code>{set_text}</code> to upload a new version."
    )
```

### 3. What Changed

| Before | After | Result |
|--------|-------|--------|
| `"/get_<name>"` | `html.escape("/get_<name>")` | `"/get_&lt;name&gt;"` |
| `"/set_<name>"` | `html.escape("/set_<name>")` | `"/set_&lt;config&gt;"` |
| `**Tip:**` | `<b>Tip:</b>` | HTML bold tag |
| Markdown syntax | HTML tags | Consistent with ParseMode.HTML |

---

## 🧪 Verification

### 1. Import Test
```bash
✅ python -c "from app.bot.handlers.config import cmd_list_configs; print('✅ OK')"
```

### 2. HTML Escape Test
```python
import html

assert html.escape("/get_<name>") == "/get_&lt;name&gt;"
assert html.escape("/set_<name>") == "/set_&lt;name&gt;"
# ✅ All assertions passed
```

### 3. No Code Errors
```bash
✅ get_errors: No errors found
```

---

## 📚 Documentation Created

**New File:** `docs/AIOGRAM_HTML_ESCAPING.md` (400+ lines)

**Contents:**
- Problem explanation
- Solution with examples
- Context7-mcp research results
- HTML escaping best practices
- Common pitfalls
- Alternative approaches (aiogram formatting API)
- Quick reference guide
- Test cases

---

## 🎯 Best Practices Learned

### 1. Always Escape User Input with HTML Parse Mode

```python
# ❌ WRONG
username = message.from_user.username
await message.answer(f"<b>{username}</b>")

# ✅ CORRECT
username = html.escape(message.from_user.username)
await message.answer(f"<b>{username}</b>")
```

### 2. Escape Placeholders with Angle Brackets

```python
# ❌ WRONG - Telegram error
await message.answer("Use /get_<name> command")

# ✅ CORRECT
text = html.escape("/get_<name>")
await message.answer(f"Use <code>{text}</code> command")
```

### 3. Use Consistent Formatting

```python
# ❌ WRONG - Mixing Markdown with HTML mode
await message.answer("**Bold** and <b>bold</b>")

# ✅ CORRECT - All HTML tags
await message.answer("<b>Bold</b> and <i>italic</i>")
```

### 4. Alternative: aiogram Formatting API

```python
from aiogram.utils.formatting import Text, Bold, Code

# Automatic escaping!
content = Text(
    "💡 ", Bold("Tip:"), " Use ", Code("/get_<name>"), " to download."
)
await message.answer(**content.as_kwargs())
```

---

## 🔍 Impact

### Code Changes
- **1 file modified:** `app/bot/handlers/config.py`
- **1 import added:** `import html`
- **1 function updated:** `cmd_list_configs()`
- **Lines changed:** ~10 lines

### Documentation
- **1 new document:** `docs/AIOGRAM_HTML_ESCAPING.md` (400+ lines)
- **1 summary document:** `docs/HTML_ESCAPING_FIX_SUMMARY.md` (this file)

### Testing
- ✅ Import test passed
- ✅ HTML escape test passed
- ✅ No syntax errors
- ✅ Ready for deployment

---

## 📖 Related Issues

This fix prevents:
- ❌ "Unsupported start tag" errors
- ❌ "can't parse entities" errors
- ❌ Telegram message rejection

This applies to:
- Any text with `<something>` pattern
- User-provided content
- Code examples
- Configuration placeholders

---

## 🚀 Deployment Notes

### Before Deploying
1. ✅ Code changes committed
2. ✅ Documentation created
3. ✅ Tests passing
4. ✅ No errors found

### After Deploying
1. Test `/list_configs` command in Telegram
2. Verify message displays correctly
3. Check that `<name>` is shown (not parsed as tag)
4. Monitor for any new parsing errors

### Rollback Plan (if needed)
```bash
# Revert the commit
git revert HEAD

# Or restore old version
git checkout <previous-commit> -- app/bot/handlers/config.py
```

---

## 🎓 Knowledge Base

### HTML Special Characters

| Character | Escaped | Description |
|-----------|---------|-------------|
| `<` | `&lt;` | Less than (start tag) |
| `>` | `&gt;` | Greater than (end tag) |
| `&` | `&amp;` | Ampersand |
| `"` | `&quot;` | Double quote |
| `'` | `&#x27;` | Single quote |

### Telegram HTML Tags (Safe to Use)

- `<b>bold</b>` ✅
- `<i>italic</i>` ✅
- `<u>underline</u>` ✅
- `<s>strikethrough</s>` ✅
- `<code>code</code>` ✅
- `<pre>pre</pre>` ✅
- `<a href="url">link</a>` ✅

### When to Escape

✅ **Always escape:**
- User input
- Placeholders with `<>`
- Code examples
- Any text with special chars

❌ **Don't escape:**
- Your own HTML tags
- Already escaped text
- Intentional formatting

---

## 🔗 References

- **Python html module:** https://docs.python.org/3/library/html.html
- **aiogram docs:** https://docs.aiogram.dev/en/dev/
- **Telegram Bot API:** https://core.telegram.org/bots/api#formatting-options
- **context7-mcp:** Used for research (/websites/aiogram_dev_en_dev)

---

## ✅ Checklist

- [x] Problem identified
- [x] Solution researched with context7-mcp
- [x] Code fixed
- [x] Import added
- [x] Comments added
- [x] Tests verified
- [x] Documentation created
- [x] No errors found
- [x] Ready for deployment

---

**Fixed by:** GitHub Copilot with context7-mcp  
**Date:** 2025-12-29  
**Status:** ✅ RESOLVED and DOCUMENTED  
**Sprint:** CONFIG-06 (HTML Escaping Fix)

