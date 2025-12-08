/**
 * Constants Configuration
 * Single source of truth for all magic numbers and configuration values
 * Synchronized with backend constraints (app/calculation/models.py)
 */

// Validation constraints (must match app/calculation/models.py)
export const Constraints = {
    // Year validation (synchronized with models.py @field_validator)
    YEAR_MIN: 1990,
    YEAR_MAX: () => new Date().getFullYear(), // Dynamic: current year

    // Engine volume validation (models.py: engine_cc: int = Field(gt=0))
    ENGINE_CC_MIN: 500,
    ENGINE_CC_MAX: 10000,

    // NEW 2025: Engine power validation (models.py: engine_power_hp)
    ENGINE_POWER_HP_MIN: 1,
    ENGINE_POWER_HP_MAX: 1500,

    // Price validation (models.py: purchase_price: Decimal = Field(gt=0))
    PRICE_MIN: 1,

    // Input steps
    ENGINE_CC_STEP: 50,
    PRICE_STEP: 0.01,
};

// NEW 2025: Conversion factors
/**
 * Conversion factors for units of measurement.
 * Synchronized with GET /api/meta response.
 */
export const CONVERSION_FACTORS = {
    HP_TO_KW: 0.7355,      // horsepower → kilowatts
    KW_TO_HP: 1.35962      // kilowatts → horsepower (inverse)
};

// NEW 2025-12-08: Hint thresholds for visual hints system (MVP)
/**
 * Thresholds for visual hints on critical form fields.
 * Based on optimal customs duty and utilization fee calculations.
 * References:
 * - docs/QUICK_REFERENCE_AGE_OPTIMAL.md (age thresholds)
 * - docs/QUICK_REFERENCE_POWER_LIMITS.md (power thresholds)
 */
export const HINT_THRESHOLDS = {
    // Age thresholds (years from current year)
    AGE: {
        OPTIMAL_MIN: 3,    // Minimum age for optimal zone (3-5 years)
        OPTIMAL_MAX: 5     // Maximum age for optimal zone
    },
    // Engine power thresholds (horsepower)
    POWER: {
        OPTIMAL_MAX: 160,      // Up to 160 HP: minimal utilization fee
        ACCEPTABLE_MAX: 200,   // 160-200 HP: fee starts increasing
        WARNING_MAX: 300       // 200-300 HP: high risk zone, >300 HP: prohibitive
    }
};

// API endpoints
export const API_ENDPOINTS = {
    CALCULATE: '/api/calculate',
    META: '/api/meta',
    RATES: '/api/rates',
    REFRESH_RATES: '/api/rates/refresh',
    HEALTH: '/api/health',
};

// API request configuration
export const API_CONFIG = {
    RETRY_COUNT: 3,
    RETRY_DELAY: 1000, // milliseconds
    TIMEOUT: 10000, // 10 seconds
    MAX_PAYLOAD_SIZE: 4096, // Telegram payload limit in bytes
    MAX_SUMMARY_BYTES: 3000, // Leave room for metadata
};

// Default form values
export const DEFAULT_VALUES = {
    COUNTRY: 'japan',
    FREIGHT_TYPE: 'standard',
    VEHICLE_TYPE: 'M1',
    CURRENCY: 'JPY',
    YEAR_OFFSET: 3, // Default: current year - 3
    ENGINE_CC: 1500,
};

// Country emoji mapping (synchronized with backend meta API)
// Note: Backend uses fruit emojis as per FLAG_TO_FRUIT_MIGRATION.md
export const COUNTRY_EMOJI = {
    japan: '🍇',
    korea: '🍊',
    uae: '🍉',
    china: '🍑',
    georgia: '🍒',
};

// Freight type codes
export const FREIGHT_TYPES = {
    STANDARD: 'standard',
    OPEN: 'open',
    CONTAINER: 'container',
};

// Vehicle type codes (synchronized with models.py VehicleType literal)
export const VEHICLE_TYPES = {
    M1: 'M1',
    PICKUP: 'pickup',
    BUS: 'bus',
    MOTORHOME: 'motorhome',
    OTHER: 'other',
};

// Currency codes (must match backend rates configuration)
export const CURRENCIES = {
    JPY: 'JPY',
    USD: 'USD',
    EUR: 'EUR',
    CNY: 'CNY',
    AED: 'AED',
    RUB: 'RUB',
};

// Age categories (must match backend calculation engine)
export const AGE_CATEGORIES = {
    LT3: 'lt3',      // Less than 3 years
    FROM_3_TO_5: '3_5', // 3 to 5 years
    GT5: 'gt5',      // Greater than 5 years
};

// Haptic feedback types (Telegram WebApp)
export const HAPTIC_TYPES = {
    LIGHT: 'light',
    MEDIUM: 'medium',
    HEAVY: 'heavy',
};

// Toast/notification types
export const TOAST_TYPES = {
    INFO: 'info',
    SUCCESS: 'success',
    ERROR: 'error',
    WARNING: 'warning',
};

// Toast configuration
export const TOAST_CONFIG = {
    DURATION: 3000, // milliseconds
    COLORS: {
        info: '#3b82f6',
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
    },
};

// CSS animation durations
export const ANIMATION = {
    SLIDE_UP: 300, // milliseconds
    FADE: 200,
    TELEGRAM_CLOSE_DELAY: 800,
};

// Form input debounce delay
export const DEBOUNCE = {
    INPUT: 300, // milliseconds
    SEARCH: 500,
};

// Fallback metadata (used if /api/meta fails)
export const FALLBACK_META = {
    countries: [
        { code: 'japan', label: 'Япония', emoji: '🇯🇵', purchase_currency: 'JPY', freight_types: ['standard'] },
        { code: 'korea', label: 'Корея', emoji: '🇰🇷', purchase_currency: 'USD', freight_types: ['standard'] },
        { code: 'uae', label: 'ОАЭ', emoji: '🇦🇪', purchase_currency: 'AED', freight_types: ['open', 'container'] },
        { code: 'china', label: 'Китай', emoji: '🇨🇳', purchase_currency: 'USD', freight_types: ['open'] },
        { code: 'georgia', label: 'Грузия', emoji: '🇬🇪', purchase_currency: 'USD', freight_types: ['open'] },
    ],
    freight_type_labels: {
        standard: 'Стандартный',
        open: 'Открытый',
        container: 'Контейнер',
    },
};

// Form field IDs (for easier refactoring)
export const FORM_FIELDS = {
    COUNTRY_SELECT: 'countrySelect',
    YEAR: 'year',
    ENGINE_CC: 'engineCc',
    PURCHASE_PRICE: 'purchasePrice',
    CURRENCY: 'currency',
    VEHICLE_TYPE: 'vehicleType',
    FREIGHT_OPTIONS: 'freightOptions',
    FREIGHT_GRID: 'freightGrid',
};

// Result display element IDs
export const RESULT_ELEMENTS = {
    CARD: 'resultCard',
    TOTAL_AMOUNT: 'totalAmount',
    BREAKDOWN: 'breakdown',
    META_INFO: 'metaInfo',
    SHARE_BTN: 'shareBtn',
};

// UI element IDs
export const UI_ELEMENTS = {
    FORM: 'calculatorForm',
    CALCULATE_BTN: 'calculateBtn',
    LOADING: 'loading',
    ERROR: 'error',
    BACK_BTN: 'backToCalcBtn',
};

// Export default for convenience
export default {
    Constraints,
    API_ENDPOINTS,
    API_CONFIG,
    DEFAULT_VALUES,
    COUNTRY_EMOJI,
    FREIGHT_TYPES,
    VEHICLE_TYPES,
    CURRENCIES,
    AGE_CATEGORIES,
    HAPTIC_TYPES,
    TOAST_TYPES,
    TOAST_CONFIG,
    ANIMATION,
    DEBOUNCE,
    FALLBACK_META,
    FORM_FIELDS,
    RESULT_ELEMENTS,
    UI_ELEMENTS,
};

