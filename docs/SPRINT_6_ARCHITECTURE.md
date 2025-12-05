# UI Module Architecture - Sprint 6

## Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│                     index.html (Main App)                    │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │          Import UI Module (RPG Sprint 6)            │     │
│  │  import { ui } from '/static/js/modules/ui.js'     │     │
│  └────────────────────────────────────────────────────┘     │
│                            │                                  │
│                            ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Replace old functions with ui.* methods:           │    │
│  │  • showError() → ui.showError()                     │    │
│  │  • showLoading() → ui.showLoading()                 │    │
│  │  • hideResult() → ui.hideResult()                   │    │
│  │  • showToast() → ui.showToast()                     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               js/modules/ui.js (391 lines)                   │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │                    UI Class                         │     │
│  │  ┌──────────────────────────────────────────┐      │     │
│  │  │  State Management (FSM)                  │      │     │
│  │  │  • _state: idle/loading/error/success    │      │     │
│  │  │  • getState() → string                   │      │     │
│  │  │  • _setState(newState)                   │      │     │
│  │  └──────────────────────────────────────────┘      │     │
│  │                                                      │     │
│  │  ┌──────────────────────────────────────────┐      │     │
│  │  │  Public Methods (UI Control)             │      │     │
│  │  │  • showLoading(text?)                    │      │     │
│  │  │  • hideLoading()                         │      │     │
│  │  │  • showError(message)                    │      │     │
│  │  │  • hideError()                           │      │     │
│  │  │  • showResult()                          │      │     │
│  │  │  • hideResult()                          │      │     │
│  │  │  • showShareButton() / hideShareButton() │      │     │
│  │  │  • scrollToResult()                      │      │     │
│  │  │  • disableForm() / enableForm()          │      │     │
│  │  │  • showToast(msg, type, duration)        │      │     │
│  │  │  • reset()                               │      │     │
│  │  └──────────────────────────────────────────┘      │     │
│  │                                                      │     │
│  │  ┌──────────────────────────────────────────┐      │     │
│  │  │  Private Methods (Internal)              │      │     │
│  │  │  • _cacheElements() → cache DOM refs     │      │     │
│  │  │  • _initializeARIA() → set ARIA attrs    │      │     │
│  │  │  • _fadeIn(element) → CSS animation      │      │     │
│  │  │  • _fadeOut(element) → CSS animation     │      │     │
│  │  │  • _hapticFeedback(type) → Telegram     │      │     │
│  │  └──────────────────────────────────────────┘      │     │
│  └────────────────────────────────────────────────────┘     │
│                                                               │
│  Export: ui (singleton), UI class, UI_STATES enum            │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
┌─────────────────────────┐   ┌──────────────────────┐
│  css/components.css     │   │  DOM Elements        │
│  • @keyframes slideUp   │   │  • #loading          │
│  • @keyframes slideDown │   │  • #error            │
│  • .toast styles        │   │  • #resultCard       │
└─────────────────────────┘   │  • #shareBtn         │
                              │  • #calculateBtn     │
                              │  • #calculatorForm   │
                              └──────────────────────┘
```

## State Machine Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    UI State Machine                          │
└─────────────────────────────────────────────────────────────┘

         ┌──────────┐
         │   IDLE   │ ◄──────────────────────┐
         └─────┬────┘                        │
               │                             │
   showLoading()│                        reset()
               │                             │
               ▼                             │
         ┌──────────┐                        │
         │ LOADING  │                        │
         └─────┬────┘                        │
               │                             │
      ┌────────┴────────┐                   │
      │                 │                   │
  showResult()      showError()             │
      │                 │                   │
      ▼                 ▼                   │
┌──────────┐      ┌──────────┐             │
│ SUCCESS  │      │  ERROR   │             │
└─────┬────┘      └─────┬────┘             │
      │                 │                   │
      └────────┬────────┘                   │
               │                            │
         hideResult() /                     │
         hideError()                        │
               └────────────────────────────┘
```

## Method Call Flow

```
User Action: Click "Calculate"
      │
      ▼
calculateCost()
      │
      ├─► ui.showLoading('Рассчитываем...')
      │       │
      │       ├─► _setState(LOADING)
      │       ├─► _fadeIn(loadingElement)
      │       ├─► disableForm()
      │       ├─► hideError()
      │       ├─► hideResult()
      │       └─► _hapticFeedback('light')
      │
      ├─► API call...
      │
      ▼
   Success?
      │
      ├── YES ──► displayResult(result)
      │               │
      │               └─► ui.showResult()
      │                       │
      │                       ├─► _setState(SUCCESS)
      │                       ├─► addClass(resultCard, 'show')
      │                       ├─► hideLoading()
      │                       ├─► hideError()
      │                       ├─► showShareButton()
      │                       ├─► scrollToResult()
      │                       └─► _hapticFeedback('medium')
      │
      └── NO ──► catch(error)
                      │
                      └─► ui.showError(message)
                              │
                              ├─► _setState(ERROR)
                              ├─► _fadeIn(errorElement)
                              ├─► focus(errorElement)
                              ├─► hideLoading()
                              ├─► hideResult()
                              └─► _hapticFeedback('heavy')
```

## Toast Notification Flow

```
User Action: Share result
      │
      ▼
shareResult()
      │
      ├─► Copy to clipboard
      │       │
      │       └─► ui.showToast('Скопировано!', 'success')
      │               │
      │               ├─► Create toast element
      │               ├─► Set colors based on type
      │               ├─► Apply styles (fixed, bottom, centered)
      │               ├─► Add to body with slideUp animation
      │               ├─► _hapticFeedback(based on type)
      │               └─► Auto-dismiss after duration
      │                       │
      │                       └─► slideDown animation → remove()
      │
      └─► Send to Telegram
              │
              └─► ui.showToast('Отправлено в чат', 'success')
```

## ARIA Attributes Structure

```
┌─────────────────────────────────────────┐
│          Accessibility Layer             │
└─────────────────────────────────────────┘

<div id="loading" 
     role="status"              ← Screen reader announces
     aria-live="polite">        ← Non-intrusive updates
  Рассчитываем стоимость...
</div>

<div id="error" 
     role="alert"               ← Immediate announcement
     aria-live="assertive"      ← High priority
     tabindex="-1">             ← Can receive focus
  Ошибка валидации
</div>

<div id="resultCard" 
     role="region"              ← Landmark region
     aria-label="Результаты">   ← Region label
  [Result content]
</div>

<button id="calculateBtn"
        aria-busy="true">       ← Loading state
  Рассчитать
</button>
```

## Integration with Other Modules

```
┌──────────────────────────────────────────────────────────┐
│                    Module Integration                     │
└──────────────────────────────────────────────────────────┘

┌────────────┐
│  api.js    │ ──────► ui.showLoading()
│  (Sprint 5)│         ui.showError()
└────────────┘         ui.hideLoading()

┌────────────┐
│validator.js│ ──────► ui.showError()
│ (Sprint 4) │
└────────────┘

┌────────────┐
│messages.js │ ──────► Messages.errors.*
│ (Sprint 3) │         Messages.info.*
└────────────┘

┌────────────┐
│constants.js│ ──────► HAPTIC_TYPES.*
│ (Sprint 3) │         ANIMATION.*
└────────────┘

┌────────────┐
│   dom.js   │ ◄────── _fadeIn(), _fadeOut()
│ (Sprint 2) │         (could use, but ui.js
└────────────┘          implements directly)
```

## File Dependencies

```
index.html
    ├── ui.js (THIS MODULE)
    │   ├── DOM elements (cached)
    │   ├── CSS animations
    │   └── Telegram WebApp API
    ├── api.js
    ├── validator.js
    ├── messages.js
    ├── constants.js
    └── formatters.js
```

---

## Key Design Decisions

### 1. Singleton Pattern
**Why**: Only one UI state manager needed per app
**Benefit**: Global access, single source of truth

### 2. State Machine
**Why**: Prevent invalid UI states
**Benefit**: Predictable behavior, easier debugging

### 3. DOM Caching
**Why**: Performance optimization
**Benefit**: No repeated `getElementById()` calls

### 4. CSS Animations
**Why**: Better performance than JS animations
**Benefit**: Hardware acceleration, 60 FPS

### 5. ARIA First
**Why**: Accessibility is not optional
**Benefit**: Inclusive design, better UX for all

### 6. Haptic Feedback
**Why**: Native mobile feel in Telegram
**Benefit**: Professional UX, better engagement

---

**Architecture Status**: ✅ Production Ready

