refactor(webapp): SPRINT 3 - Constants and Configuration (Single Source of Truth)

Implemented RPG "Single Source of Truth" principle by extracting ALL magic 
numbers and hardcoded strings into centralized configuration modules.

Created:
- app/webapp/js/config/messages.js (158 lines)
  * Messages.errors - validation and error messages (12 constants)
  * Messages.buttons - button labels (6 constants)
  * Messages.labels - form field labels (12 constants)
  * Messages.breakdown - cost components (8 constants)
  * Messages.info - toast notifications (8 constants)
  * Messages.warnings - warnings (4 constants)
  * Messages.share - share templates (5 constants)
  * Messages.age/freight/vehicle/countries/currencies - fallback labels

- app/webapp/js/config/constants.js (201 lines)
  * Constraints - validation limits synchronized with models.py
    - YEAR_MIN=1990 ↔ models.py @field_validator
    - ENGINE_CC_MIN/MAX=500/10000
    - PRICE_MIN=1
  * API_ENDPOINTS - all API paths
  * API_CONFIG - request configuration (retry, timeout, payload limits)
  * DEFAULT_VALUES - form defaults (COUNTRY='japan', ENGINE_CC=1500, YEAR_OFFSET=3)
  * COUNTRY_EMOJI - fruit emojis (japan=🍇, korea=🍊, uae=🍉, china=🍑, georgia=🍒)
  * FALLBACK_META - offline metadata
  * UI constants (HAPTIC_TYPES, TOAST_CONFIG, ANIMATION, DEBOUNCE)

Changed:
- app/webapp/index.html
  * Added imports for Messages and Constants
  * Replaced 50+ hardcoded strings with Messages constants
  * Replaced 15+ magic numbers with Constraints/DEFAULT_VALUES
  * Replaced API URLs with API_ENDPOINTS
  * Replaced fallback metadata with FALLBACK_META
  * Replaced haptic types with HAPTIC_TYPES
  * Created applyFormConstraints() function for dynamic constraint application

Updated documentation:
- docs/rpg.yaml - SPRINT_3_COMPLETED status, added messages.js and constants.js entries
- docs/webapp_refactoring_checklist.md - marked Этап 3 as completed
- CHANGELOG_georgia.md - added SPRINT 3 entry
- docs/SPRINT_3_COMPLETED.md - full sprint documentation

Benefits:
✓ Zero magic numbers - all numeric constraints in one place
✓ Zero hardcoded strings - all UI text in one place
✓ Easy localization - add messages_en.js, messages_de.js
✓ Easy rebranding - change all texts in 1 file
✓ Type-safe - clear constant names prevent typos
✓ Maintainable - change validation limit once, updates everywhere
✓ Testable - import constants in tests
✓ Backend sync - frontend/backend validation in harmony

Testing:
- node -c messages.js ✓
- node -c constants.js ✓
- Manual testing: all messages display correctly
- No console errors

BREAKING CHANGES: None (backward compatible, all changes are internal)

Refs: docs/webapp_refactoring_plan.md (Этап 3)

