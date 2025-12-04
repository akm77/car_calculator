# CSS Modules Reference Guide

Quick reference for the modular CSS architecture created in Sprint 1.

---

## 📁 File Structure

```
app/webapp/css/
├── variables.css   (45 lines)  - Design tokens & CSS variables
├── base.css        (75 lines)  - Foundation styles & reset
├── components.css  (288 lines) - UI components & widgets
└── telegram.css    (67 lines)  - Telegram WebApp integration
```

---

## 1️⃣ variables.css - Design Tokens

### Telegram Theme Colors
```css
--bg-color              /* Background color from Telegram theme */
--text-color            /* Primary text color */
--hint-color            /* Secondary/hint text color */
--link-color            /* Link and accent color */
--button-color          /* Primary button background */
--button-text-color     /* Button text color */
--secondary-bg-color    /* Cards and secondary surfaces */
```

### Spacing Scale
```css
--spacing-xs    /* 6px  - Minimal spacing */
--spacing-sm    /* 8px  - Small spacing */
--spacing-md    /* 12px - Medium spacing */
--spacing-lg    /* 16px - Large spacing */
--spacing-xl    /* 20px - Extra large */
--spacing-xxl   /* 24px - Double extra large */
```

### Typography Scale
```css
--font-size-xs    /* 12px - Small text, meta info */
--font-size-sm    /* 14px - Labels, hints */
--font-size-base  /* 16px - Body text, inputs */
--font-size-lg    /* 18px - Buttons */
--font-size-xl    /* 24px - Headings */
--font-size-xxl   /* 28px - Result amounts */
```

### Layout
```css
--border-radius        /* 12px - Default border radius */
--border-radius-small  /* 6px  - Small elements */
--border-radius-medium /* 8px  - Medium elements */
--shadow               /* Box shadow for cards */
```

---

## 2️⃣ base.css - Foundation

### Global Reset
```css
* { margin: 0; padding: 0; box-sizing: border-box; }
```

### Body & Container
```css
body              /* Base styles, padding, font-family */
.container        /* Max-width 480px, centered */
```

### Typography
```css
.header           /* Page header */
.header h1        /* Main heading */
.header p         /* Subtitle */
label             /* Form labels */
.required         /* Required field indicator */
```

### Animations
```css
@keyframes slideUp  /* Fade in from bottom */
@keyframes spin     /* Loading spinner rotation */
```

---

## 3️⃣ components.css - UI Components

### Cards
```css
.form-card        /* Input form container */
.result-card      /* Results display container */
.result-card.show /* Visible state with animation */
```

### Forms
```css
.form-group       /* Form field wrapper */
input, select     /* Base input styling */
.input-group      /* Horizontal input layout */
.currency-select  /* Currency dropdown (100px fixed) */
```

### Country Selector
```css
.country-selector  /* Wrapper */
.country-dropdown  /* Main select element */
.country-option    /* Option items */
```

### Freight Options
```css
.freight-options      /* Container */
.freight-options.show /* Visible state */
.freight-grid         /* Flex grid layout */
.freight-btn          /* Individual freight option */
.freight-btn.active   /* Selected state */
```

### Buttons
```css
.calculate-btn    /* Primary action button */
.share-btn        /* Secondary outline button */
.back-btn         /* Navigation button */
```

### Results Display
```css
.result-total         /* Total amount card */
.result-total .amount /* Large number display */
.result-total .label  /* Description text */
```

### Breakdown
```css
.breakdown-item        /* Individual line item */
.breakdown-item:last-child /* Total line (bold, top border) */
.breakdown-label       /* Item label */
.breakdown-amount      /* Item amount */
```

### States
```css
.loading          /* Loading indicator */
.loading:after    /* Spinning circle animation */
.error            /* Error message box */
.meta-info        /* Additional information */
```

### Tabs
```css
.tabs             /* Tab container */
.tab-nav          /* Tab navigation (hidden) */
.tab-btn          /* Tab button */
.tab-btn.active   /* Active tab */
.tab-panes        /* Tab content container */
.tab-pane         /* Individual tab content */
.tab-pane.active  /* Visible tab */
```

---

## 4️⃣ telegram.css - Platform Integration

### Theme Transitions
```css
body              /* Smooth theme color transitions */
input, select     /* Theme-aware transitions */
.form-card        /* Card transitions */
.result-card      /* Result transitions */
```

### Mobile Optimizations
```css
.container        /* Safe area insets for notches */
button, .btn      /* 44px minimum touch target */
```

### Viewport Support
```css
@supports (padding: max(0px))  /* Safe area inset support */
```

### User Experience
```css
.calculate-btn, .share-btn, etc.  /* Disabled text selection */
```

---

## 🎨 Usage Examples

### Using CSS Variables in Custom Styles
```css
.my-custom-element {
    color: var(--text-color);
    padding: var(--spacing-md);
    border-radius: var(--border-radius-small);
    font-size: var(--font-size-base);
}
```

### Responsive Button
```css
.my-button {
    padding: var(--spacing-md) var(--spacing-lg);
    background: var(--button-color);
    color: var(--button-text-color);
    border-radius: var(--border-radius-medium);
    min-height: 44px; /* iOS touch target */
}
```

### Animated Card
```css
.my-card {
    background: var(--secondary-bg-color);
    padding: var(--spacing-xl);
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    animation: slideUp 0.3s ease-out;
}
```

---

## 🔧 Customization Guide

### Adding a New Color
1. Add to `variables.css`:
   ```css
   --success-color: #28a745;
   --warning-color: #ffc107;
   ```

2. Use in components:
   ```css
   .success-message { color: var(--success-color); }
   ```

### Adding a New Spacing Value
```css
/* In variables.css */
--spacing-xxxl: 32px;

/* Use in components */
.large-card {
    padding: var(--spacing-xxxl);
}
```

### Adding a New Component
Create styles in `components.css`:
```css
/* New Component: Badge */
.badge {
    display: inline-block;
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--link-color);
    color: var(--button-text-color);
    border-radius: var(--border-radius-small);
    font-size: var(--font-size-xs);
    font-weight: 600;
}
```

---

## 🎯 Best Practices

### DO ✅
- Use CSS variables for consistency
- Follow BEM-like naming (`.component__element--modifier`)
- Add comments for complex selectors
- Group related styles together
- Use the spacing scale for consistency

### DON'T ❌
- Hard-code colors (use variables)
- Hard-code spacing values
- Use `!important` (except `.tab-nav` special case)
- Add inline styles in HTML
- Duplicate styles across files

---

## 📊 File Loading Order

**Important**: CSS files must be loaded in this order:

```html
<link rel="stylesheet" href="/static/css/variables.css">  <!-- 1. Variables first -->
<link rel="stylesheet" href="/static/css/base.css">       <!-- 2. Base styles -->
<link rel="stylesheet" href="/static/css/components.css"> <!-- 3. Components -->
<link rel="stylesheet" href="/static/css/telegram.css">   <!-- 4. Platform overrides -->
```

This ensures:
1. Variables are available to all other files
2. Base styles are established before components
3. Component styles build on the base
4. Platform-specific overrides apply last

---

## 🔍 Debugging Tips

### Check if CSS is loaded
```javascript
// In browser console
document.styleSheets[0].href  // Should show /static/css/variables.css
```

### Verify CSS variables
```javascript
// In browser console
getComputedStyle(document.documentElement).getPropertyValue('--bg-color')
```

### Test Telegram theme integration
```javascript
// In browser console (Telegram WebApp only)
Telegram.WebApp.colorScheme  // 'light' or 'dark'
```

---

## 📚 Related Documentation

- **Sprint 1 Completion**: `docs/SPRINT_1_COMPLETED.md`
- **Refactoring Plan**: `docs/webapp_refactoring_plan.md`
- **Checklist**: `docs/webapp_refactoring_checklist.md`
- **Changelog**: `CHANGELOG_georgia.md`

---

**Last Updated**: December 5, 2025  
**Sprint**: 1 (CSS Extraction)  
**Status**: ✅ Complete and Production Ready

