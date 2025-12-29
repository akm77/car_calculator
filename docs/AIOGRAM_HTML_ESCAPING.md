# HTML Escaping in aiogram - Best Practices

**Date:** 2025-12-29  
**Context:** Fix for Telegram "Bad Request: can't parse entities" error  
**Solution:** Using `html.escape()` for special characters

---

## 🐛 Problem

When using `ParseMode.HTML` in aiogram, Telegram interprets angle brackets `<>` as HTML tags. If the text contains `<name>` or similar patterns, Telegram will try to parse them as HTML tags and fail with:

```
Telegram server says - Bad Request: can't parse entities: 
Unsupported start tag "name" at byte offset 475
```

---

## ✅ Solution

Use Python's built-in `html.escape()` function to escape special HTML characters:

### Before (❌ ERROR)

```python
await message.answer(
    f"💡 **Tip:** Use `/get_<name>` to download a config file.\n"
    f"📤 Use `/set_<name>` to upload a new version."
)
```

**Error:** `<name>` is interpreted as HTML tag → **Telegram rejects the message**

### After (✅ FIXED)

```python
import html

# Escape the angle brackets
tip_text = html.escape("/get_<name>")
set_text = html.escape("/set_<name>")

await message.answer(
    f"💡 <b>Tip:</b> Use <code>{tip_text}</code> to download a config file.\n"
    f"📤 Use <code>{set_text}</code> to upload a new version."
)
```

**Result:** 
- `<name>` → `&lt;name&gt;` (safe for HTML)
- Telegram correctly displays: `/get_<name>`

---

## 📚 Context7-mcp Research

Used **context7-mcp** to find the solution:

```bash
# 1. Search for aiogram library
resolve-library-id "aiogram telegram bot markdown html escape"

# Result: /websites/aiogram_dev_en_dev (88.8 score, 6,751 snippets)

# 2. Get documentation
get-library-docs /websites/aiogram_dev_en_dev
  --mode code
  --topic "html escape special characters markdown parse mode formatting"
```

**Key Finding from aiogram docs:**

```python
import html
from aiogram.types import ParseMode

await message.answer(
    text=f"Hello, <b>{html.quote(message.from_user.full_name)}</b>!",
    parse_mode=ParseMode.HTML
)
```

---

## 🔧 HTML Escaping Functions

Python provides two main functions for HTML escaping:

### 1. `html.escape()` - General Purpose

```python
import html

# Escapes: < > & " '
text = html.escape("<script>alert('XSS')</script>")
# Result: &lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;

# Use for any user-provided text in HTML context
safe_text = html.escape(user_input)
await message.answer(f"<b>User said:</b> {safe_text}")
```

**Escapes:**
- `<` → `&lt;`
- `>` → `&gt;`
- `&` → `&amp;`
- `"` → `&quot;` (optional, use `quote=True`)
- `'` → `&#x27;` (optional, use `quote=True`)

### 2. `html.quote()` - For Attributes (Deprecated in Python 3.8+)

```python
import html

# Deprecated: Use html.escape() instead
text = html.escape(user_input, quote=True)
```

**Note:** `html.quote()` is deprecated. Use `html.escape(text, quote=True)` for attributes.

---

## 🎯 When to Use HTML Escaping

### ✅ Always Escape

1. **User-provided text:**
   ```python
   username = html.escape(message.from_user.username)
   await message.answer(f"Hello, <b>{username}</b>!")
   ```

2. **Text with angle brackets:**
   ```python
   code = html.escape("if (x < 5 && y > 10)")
   await message.answer(f"<code>{code}</code>")
   ```

3. **Placeholders in messages:**
   ```python
   placeholder = html.escape("<name>")
   await message.answer(f"Use /get_{placeholder}")
   ```

### ❌ Don't Escape

1. **Your own HTML tags:**
   ```python
   # This is OK - these are intentional HTML tags
   await message.answer("<b>Bold</b> and <i>italic</i>")
   ```

2. **Already escaped text:**
   ```python
   # Don't double-escape
   text = html.escape(user_input)
   # ❌ BAD: text = html.escape(text)  # Double escaping!
   ```

---

## 📖 Alternative: aiogram's Formatting API

aiogram provides a high-level formatting API that handles escaping automatically:

### Using Text and Code Classes

```python
from aiogram.utils.formatting import Text, Bold, Code

# No manual escaping needed!
content = Text(
    "💡 ", Bold("Tip:"), " Use ", Code("/get_<name>"), " to download a config file."
)

await message.answer(**content.as_kwargs())
```

**Benefits:**
- ✅ Automatic HTML escaping
- ✅ Type-safe
- ✅ Cleaner code
- ✅ Less error-prone

**Example with our case:**

```python
from aiogram.utils.formatting import Text, Bold, Code

@router.message(Command("list_configs"))
async def cmd_list_configs(message: Message):
    config_list = format_config_list()
    
    content = Text(
        config_list, "\n",
        "💡 ", Bold("Tip:"), " Use ", Code("/get_<name>"), " to download a config file.\n",
        "📤 Use ", Code("/set_<name>"), " to upload a new version."
    )
    
    await message.answer(**content.as_kwargs())
```

---

## 🔍 Common Pitfalls

### 1. Forgetting to Escape User Input

```python
# ❌ DANGEROUS: XSS vulnerability
username = message.from_user.username
await message.answer(f"<b>{username}</b>")  # User could inject HTML!

# ✅ SAFE: Escaped
username = html.escape(message.from_user.username)
await message.answer(f"<b>{username}</b>")
```

### 2. Escaping Your Own Tags

```python
# ❌ WRONG: Escapes the tags you want
await message.answer(html.escape("<b>Bold text</b>"))
# Result: &lt;b&gt;Bold text&lt;/b&gt; (displays literally)

# ✅ CORRECT: Only escape user content
text = html.escape(user_input)
await message.answer(f"<b>{text}</b>")
```

### 3. Using Markdown Syntax with HTML Mode

```python
# ❌ WRONG: Mixing Markdown with HTML parse mode
await message.answer("**Bold** and <b>bold</b>")  # ** won't work!

# ✅ CORRECT: Use HTML tags consistently
await message.answer("<b>Bold</b> and <i>italic</i>")
```

### 4. Angle Brackets in Code Examples

```python
# ❌ WRONG: Unescaped angle brackets
await message.answer("Use /get_<name> command")
# Error: Unsupported start tag "name"

# ✅ CORRECT: Escape or use <code> tag
await message.answer(f"Use <code>{html.escape('/get_<name>')}</code> command")
```

---

## 📋 Quick Reference

### HTML Special Characters

| Character | Unescaped | Escaped | When to Escape |
|-----------|-----------|---------|----------------|
| `<` | `<` | `&lt;` | Always (except your HTML tags) |
| `>` | `>` | `&gt;` | Always (except your HTML tags) |
| `&` | `&` | `&amp;` | Always |
| `"` | `"` | `&quot;` | In HTML attributes |
| `'` | `'` | `&#x27;` | In HTML attributes |

### Telegram HTML Tags (Don't Escape)

Safe to use without escaping:
- `<b>bold</b>`
- `<i>italic</i>`
- `<u>underline</u>`
- `<s>strikethrough</s>`
- `<code>code</code>`
- `<pre>pre-formatted</pre>`
- `<a href="url">link</a>`

---

## 🧪 Testing

```python
import html

# Test cases
test_cases = [
    ("/get_<name>", "/get_&lt;name&gt;"),
    ("<script>alert(1)</script>", "&lt;script&gt;alert(1)&lt;/script&gt;"),
    ("if (x < 5 && y > 10)", "if (x &lt; 5 &amp;&amp; y &gt; 10)"),
    ("Hello & goodbye", "Hello &amp; goodbye"),
]

for input_text, expected in test_cases:
    result = html.escape(input_text)
    assert result == expected, f"Failed: {input_text}"
    print(f"✅ {input_text} → {result}")
```

---

## 📚 References

- **Python html module:** https://docs.python.org/3/library/html.html
- **aiogram Documentation:** https://docs.aiogram.dev/en/dev/
- **Telegram Bot API - Formatting:** https://core.telegram.org/bots/api#formatting-options
- **aiogram Formatting Utils:** https://docs.aiogram.dev/en/dev/utils/formatting

---

## 🎯 Applied in Project

**File:** `app/bot/handlers/config.py`

**Change:**
```python
# Before (ERROR)
await message.answer(
    f"💡 **Tip:** Use `/get_<name>` to download a config file.\n"
    f"📤 Use `/set_<name>` to upload a new version."
)

# After (FIXED)
import html

tip_text = html.escape("/get_<name>")
set_text = html.escape("/set_<name>")

await message.answer(
    f"💡 <b>Tip:</b> Use <code>{tip_text}</code> to download a config file.\n"
    f"📤 Use <code>{set_text}</code> to upload a new version."
)
```

**Result:**
- ✅ No more "Unsupported start tag" errors
- ✅ Message displays correctly: `/get_<name>`
- ✅ Using proper HTML formatting (`<b>`, `<code>`)

---

## 💡 Best Practices Summary

1. **Always escape user input** when using `ParseMode.HTML`
2. **Use `html.escape()`** for any text containing `<`, `>`, `&`
3. **Consider aiogram's formatting API** for complex messages
4. **Test with special characters** before deployment
5. **Document which parse mode you're using** (HTML vs Markdown)
6. **Use `<code>` tags** for code examples and commands
7. **Never double-escape** already escaped text
8. **Keep formatting consistent** (all HTML or all Markdown, not mixed)

---

**Researched with:** context7-mcp (/websites/aiogram_dev_en_dev)  
**Fixed by:** GitHub Copilot  
**Date:** 2025-12-29  
**Status:** ✅ RESOLVED

