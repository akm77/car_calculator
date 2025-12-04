# How to Run Tests for Sprint 2

## Manual Test Suite

### Quick Start

1. **Start the development server** (if not running):
   ```bash
   cd /Users/admin/PycharmProjects/car_calculator
   uvicorn app.main:app --reload
   ```

2. **Open test page in browser**:
   ```
   http://localhost:8000/static/../tests/manual/test_formatters.html
   ```
   
   Or use direct file path:
   ```
   file:///Users/admin/PycharmProjects/car_calculator/tests/manual/test_formatters.html
   ```

3. **Check results**:
   - Green checkmarks = PASS
   - Red X marks = FAIL
   - Summary at top shows success rate

### Expected Results

All 26 tests should pass:
- Formatter tests: 18/18 ✅
- DOM util tests: 8/8 ✅
- Success rate: 100%

### Test Categories

#### Formatters (18 tests)
- formatNumber: handles numbers, null, invalid input
- formatCurrency: RUB, USD, handles null
- getAgeCategory: lt3, 3_5, gt5
- formatEngineVolume: valid, null
- formatYear: valid, out of range
- formatPercent: decimal formatting
- truncateToBytes: byte limit, ellipsis
- byteLength: ASCII, Cyrillic

#### DOM Utils (8 tests)
- show/hide: class manipulation
- setText: content setting
- setContent: HTML setting
- addClass/removeClass: class management
- hasClass: class detection
- getEl: element retrieval
- createElement: element creation with props
- debounce: delayed execution

## Testing in Browser Console

### Test Formatters Manually

Open browser console on http://localhost:8000/web/ and run:

```javascript
// Import modules (already imported in index.html)
// Test formatNumber
console.log(formatters.formatNumber(1234567)); // "1 234 567"
console.log(formatters.formatNumber(null)); // "—"

// Test formatCurrency
console.log(formatters.formatCurrency(1500000, 'RUB')); // "1 500 000 ₽"
console.log(formatters.formatCurrency(5000, 'USD')); // "$5 000"

// Test getAgeCategory
console.log(formatters.getAgeCategory('lt3')); // "до 3 лет"
console.log(formatters.getAgeCategory('3_5')); // "3-5 лет (проходные)"

// Test formatEngineVolume
console.log(formatters.formatEngineVolume(1500)); // "1 500 см³"
```

### Test DOM Utils Manually

```javascript
// Import modules
const testEl = document.getElementById('loading');

// Test show/hide
dom.hide(testEl);
console.log(testEl.classList.contains('show')); // false

dom.show(testEl);
console.log(testEl.classList.contains('show')); // true

// Test setText
dom.setText(testEl, 'Test Content');
console.log(testEl.textContent); // "Test Content"

// Test debounce
let counter = 0;
const debounced = dom.debounce(() => counter++, 300);
debounced();
debounced();
debounced();
setTimeout(() => console.log(counter), 400); // 1 (executed once)
```

## Testing WebApp Integration

### Verify Module Loading

1. Open http://localhost:8000/web/
2. Open Developer Tools (F12)
3. Go to Network tab
4. Reload page
5. Check for:
   - `formatters.js` - Status 200 ✅
   - `dom.js` - Status 200 ✅

### Verify Formatting Works

1. Fill out the calculator form
2. Click "Рассчитать стоимость"
3. Check that results are formatted correctly:
   - Numbers have thousand separators: "1 234 567"
   - Currency has symbols: "1 500 000 ₽"
   - Age categories are readable: "до 3 лет"

### Check Console for Errors

Should see:
- ✅ No 404 errors
- ✅ No module loading errors
- ✅ No JavaScript errors
- ✅ Meta data loaded successfully

## Troubleshooting

### Module Not Found (404)

**Problem**: `GET /static/js/utils/formatters.js 404`

**Solution**:
1. Check file exists: `ls app/webapp/js/utils/formatters.js`
2. Check main.py serves /static correctly
3. Restart server: `uvicorn app.main:app --reload`

### CORS Error

**Problem**: `Access to script blocked by CORS policy`

**Solution**:
1. Make sure you're accessing via http://localhost:8000
2. Don't use file:// protocol for module testing
3. Check main.py has CORS middleware configured

### Tests Not Running

**Problem**: Test page shows no results

**Solution**:
1. Check browser console for errors
2. Make sure ES6 modules are supported (Chrome 61+, Firefox 60+, Safari 11+)
3. Try opening in different browser
4. Check file paths in import statements

### Functions Undefined

**Problem**: `formatters is not defined`

**Solution**:
1. Check script tag has `type="module"` attribute
2. Check import statements are correct
3. Verify files are loading (Network tab)
4. Make sure functions are exported with `export function`

## Automated Testing (Future)

Currently using manual tests. For automated testing in future sprints:

```bash
# Install test framework
npm install --save-dev vitest

# Run tests
npm test
```

## CI/CD Integration (Future)

For automated testing in CI/CD pipeline:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: npm test
```

## Performance Testing

### Module Load Time

Check in Network tab:
- formatters.js: ~1-2ms
- dom.js: ~1-2ms
- Total overhead: < 5ms (negligible)

### Function Execution Time

```javascript
console.time('formatNumber');
formatters.formatNumber(1234567);
console.timeEnd('formatNumber'); // < 1ms
```

## Success Criteria

✅ All 26 tests pass  
✅ No console errors  
✅ WebApp loads correctly  
✅ Formatting works in UI  
✅ Module files accessible (200 status)  

---

**Last Updated**: December 5, 2025  
**Sprint**: 2 - Utilities Library  
**Status**: ✅ All Tests Passing

