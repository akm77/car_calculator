# 🧪 TESTING GUIDE: Bugfix 2025-12-07

## Quick Test (2 minutes)

### ✅ Step 1: Check Console Errors

1. Open browser and navigate to:
   ```
   http://localhost:8000/
   ```

2. Open DevTools Console (F12 or Cmd+Option+I)

3. **Expected results**:
   ```
   ✅ No "formValidator is not defined" errors
   ✅ No "FetchEvent resulted in network error" errors
   ✅ Only external extension messages (LastPass, ESEP - ignore these)
   ```

4. **If you see errors** → Fix not applied, check imports in index.html

---

### ✅ Step 2: Test Real-Time Validation

1. Click on "Год выпуска" field
2. Type `1900` (invalid - too old)
3. Click outside the field (blur)

**Expected**:
```
✅ Red error message appears below field
✅ Field has red border
✅ Error text: "Год должен быть между 1990 и 2025"
```

4. Clear field and type `2021` (valid)
5. Click outside

**Expected**:
```
✅ Error message disappears
✅ Red border removed
✅ No console errors
```

---

### ✅ Step 3: Test Form Validation

1. Leave all fields empty
2. Click "Рассчитать стоимость" button

**Expected**:
```
✅ Validation errors appear for all required fields
✅ Form is NOT submitted
✅ No "formValidator is not defined" errors in console
```

3. Fill in valid data:
   - Страна: Japan
   - Год: 2021
   - Объем: 1500
   - Цена: 1000000 JPY

4. Click "Рассчитать стоимость"

**Expected**:
```
✅ Form submits successfully
✅ Loading indicator appears
✅ Results displayed
✅ No errors in console
```

---

### ✅ Step 4: Test Service Worker

1. Open DevTools → Application → Service Workers
2. If SW is registered, click "Unregister"
3. Hard refresh page (Cmd+Shift+R / Ctrl+F5)
4. Navigate from `http://localhost:8000/` to app

**Expected**:
```
✅ Page loads without errors
✅ Redirect from / to /web/ works
✅ No "FetchEvent resulted in network error" in console
✅ SW registers successfully
```

---

## Full Test Suite (5 minutes)

### Test Case 1: Year Field Validation
| Input | Expected Result |
|-------|----------------|
| 1900 | ❌ Error: "Год должен быть между 1990 и 2025" |
| 1989 | ❌ Error: "Год должен быть между 1990 и 2025" |
| 1990 | ✅ Valid |
| 2021 | ✅ Valid |
| 2025 | ✅ Valid |
| 2026 | ❌ Error: "Год должен быть между 1990 и 2025" |
| empty | ❌ Error: "Поле обязательно для заполнения" |

### Test Case 2: Engine CC Field Validation
| Input | Expected Result |
|-------|----------------|
| 400 | ❌ Error: "Объем должен быть между 500 и 10000 см³" |
| 499 | ❌ Error: "Объем должен быть между 500 и 10000 см³" |
| 500 | ✅ Valid |
| 1500 | ✅ Valid |
| 10000 | ✅ Valid |
| 10001 | ❌ Error: "Объем должен быть между 500 и 10000 см³" |
| empty | ❌ Error: "Поле обязательно для заполнения" |

### Test Case 3: Purchase Price Validation
| Input | Expected Result |
|-------|----------------|
| 0 | ❌ Error: "Цена должна быть положительным числом" |
| -100 | ❌ Error: "Цена должна быть положительным числом" |
| 1 | ✅ Valid |
| 1000000 | ✅ Valid |
| empty | ❌ Error: "Поле обязательно для заполнения" |

### Test Case 4: Country Selection
| Input | Expected Result |
|-------|----------------|
| Not selected | ❌ Error: "Выберите страну покупки" |
| Japan | ✅ Valid, JPY currency, freight options appear |
| Korea | ✅ Valid, USD currency, freight options appear |
| UAE | ✅ Valid, AED currency, freight options appear |
| China | ✅ Valid, CNY currency, freight options appear |
| Georgia | ✅ Valid, USD currency, freight options appear |

---

## Known Non-Issues (Ignore These)

These console messages are **NOT errors** and can be ignored:

### 1. LastPass Extension
```
background-redux-new.js:2 WebSocket connection to 'wss://...' failed
background-redux-new.js:2 Error: Invalid frameId for foreground frameId: 0
```
**Source**: LastPass browser extension  
**Impact**: None on our app  
**Action**: Ignore

### 2. ESEP Crypto Extension
```
content.min.js:1 ESEP Crypto extension content: loading...
content.min.js:1 ESEP Crypto extension content: loaded.
```
**Source**: Browser crypto extension  
**Impact**: None on our app  
**Action**: Ignore

### 3. Telegram WebApp SDK
```
telegram-web-app.js:135 [Telegram.WebView] > postEvent web_app_set_header_color
telegram-web-app.js:135 [Telegram.WebView] > postEvent web_app_ready
telegram-web-app.js:135 [Telegram.WebView] > postEvent web_app_expand
```
**Source**: Telegram Web App SDK (debug logs)  
**Impact**: Normal behavior  
**Action**: Ignore (or disable in production)

---

## Troubleshooting

### Problem: Still seeing "formValidator is not defined"

**Solution**:
1. Hard refresh (Cmd+Shift+R / Ctrl+F5)
2. Check Network tab → validator.js loaded? (Status 200)
3. Check Console → Any import errors?
4. Verify import in index.html:
   ```javascript
   import { validator as formValidator } from '/static/js/modules/validator.js';
   ```

### Problem: Service Worker errors persist

**Solution**:
1. Unregister Service Worker:
   - DevTools → Application → Service Workers
   - Click "Unregister" next to active worker
2. Clear site data:
   - DevTools → Application → Clear storage
   - Click "Clear site data"
3. Hard refresh page
4. Check sw.js updated:
   ```javascript
   if (event.request.method !== 'GET' || event.request.url.includes('chrome-extension://')) {
       return;
   }
   ```

### Problem: Validation not triggering

**Solution**:
1. Check event listeners attached:
   ```javascript
   // In browser console:
   document.getElementById('year').addEventListener // Should exist
   ```
2. Check setupRealTimeValidation() called:
   ```javascript
   // Look in index.html around line 660
   setupRealTimeValidation(); // Should be called in init
   ```
3. Verify Constraints imported:
   ```javascript
   // Should see in imports section:
   import { Constraints } from '/static/js/config/constants.js';
   ```

---

## Success Criteria

All boxes must be checked:

- [ ] No "formValidator is not defined" errors in console
- [ ] No "FetchEvent resulted in network error" errors
- [ ] Real-time validation works on blur
- [ ] Form validation works on submit
- [ ] Invalid inputs show red error messages
- [ ] Valid inputs clear error messages
- [ ] Calculator calculates correctly with valid data
- [ ] Service Worker registers without errors
- [ ] Redirect from `/` to `/web/` works smoothly

---

## Report Results

If all tests pass:
```
✅ Bugfix verification complete
✅ All validation working correctly
✅ Service Worker fixed
✅ No console errors (except external extensions)
```

If tests fail, report:
1. Which test case failed
2. Screenshot of console errors
3. Browser and version
4. Steps to reproduce

---

**Test Duration**: 2-5 minutes  
**Last Updated**: 2025-12-07  
**Related Docs**:
- `docs/BUGFIX_2025_12_07.md` - Technical analysis
- `CHANGELOG_georgia.md` - Changelog entry
- `docs/rpg.yaml` - Dependency graph

