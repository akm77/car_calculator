/**
 * formatters.js - Pure functions for data formatting
 * RPG Methodology: Zero side effects, deterministic outputs
 * @module utils/formatters
 */

/**
 * Format number with Russian locale thousand separators
 * @param {number|string|null} num - Number to format
 * @returns {string} Formatted string or '—' if invalid
 * @example formatNumber(1234567) // "1 234 567"
 */
export function formatNumber(num) {
    if (num == null || num === '' || isNaN(Number(num))) {
        return '—';
    }
    return new Intl.NumberFormat('ru-RU', {
        maximumFractionDigits: 0
    }).format(Number(num));
}

/**
 * Format currency amount with symbol
 * @param {number|string|null} amount - Amount to format
 * @param {string} currency - Currency code (RUB, USD, JPY, etc.)
 * @returns {string} Formatted currency string or '—' if invalid
 * @example formatCurrency(1234567, 'RUB') // "1 234 567 ₽"
 */
export function formatCurrency(amount, currency = 'RUB') {
    if (amount == null || amount === '' || isNaN(Number(amount))) {
        return '—';
    }

    const value = Number(amount);
    const symbols = {
        'RUB': '₽',
        'USD': '$',
        'EUR': '€',
        'JPY': '¥',
        'CNY': '¥',
        'AED': 'AED',
        'KRW': '₩'
    };

    const formatted = new Intl.NumberFormat('ru-RU', {
        maximumFractionDigits: 0
    }).format(value);

    const symbol = symbols[currency] || currency;

    // For currencies typically written after amount
    if (['RUB', 'AED'].includes(currency)) {
        return `${formatted} ${symbol}`;
    }
    // For currencies typically written before amount
    return `${symbol}${formatted}`;
}

/**
 * Get human-readable age category label
 * @param {string} category - Age category code (lt3, 3_5, gt5)
 * @returns {string} Human-readable label
 * @example getAgeCategory('lt3') // "до 3 лет"
 */
export function getAgeCategory(category) {
    const labels = {
        'lt3': 'до 3 лет',
        '3_5': '3-5 лет (проходные)',
        'gt5': 'свыше 5 лет'
    };
    return labels[category] || category;
}

/**
 * Format engine volume in cubic centimeters
 * @param {number|string} cc - Engine volume in cc
 * @returns {string} Formatted string with unit
 * @example formatEngineVolume(1500) // "1 500 см³"
 */
export function formatEngineVolume(cc) {
    if (cc == null || cc === '' || isNaN(Number(cc))) {
        return '—';
    }
    return `${formatNumber(cc)} см³`;
}

/**
 * Format year (with validation)
 * @param {number|string} year - Year value
 * @returns {string} Formatted year or '—' if invalid
 * @example formatYear(2023) // "2023"
 */
export function formatYear(year) {
    const num = Number(year);
    if (isNaN(num) || num < 1900 || num > 2100) {
        return '—';
    }
    return String(num);
}

/**
 * Format percentage
 * @param {number|string} value - Percentage value
 * @param {number} decimals - Number of decimal places (default: 1)
 * @returns {string} Formatted percentage
 * @example formatPercent(12.5) // "12,5%"
 */
export function formatPercent(value, decimals = 1) {
    if (value == null || value === '' || isNaN(Number(value))) {
        return '—';
    }
    const num = Number(value);
    return new Intl.NumberFormat('ru-RU', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(num) + '%';
}

/**
 * Truncate string to max bytes (UTF-8) with ellipsis
 * Used for Telegram data payload limits
 * @param {string} str - String to truncate
 * @param {number} maxBytes - Maximum byte length
 * @returns {string} Truncated string
 * @example truncateToBytes('Hello World', 8) // "Hello…"
 */
export function truncateToBytes(str, maxBytes) {
    if (!str) return '';

    const encoder = new TextEncoder();
    let bytes = encoder.encode(str);

    if (bytes.length <= maxBytes) {
        return str;
    }

    // Binary search for the right cutoff point
    let low = 0;
    let high = str.length;

    while (low < high) {
        const mid = Math.floor((low + high) / 2);
        const candidate = str.slice(0, mid) + '…';
        const candidateBytes = encoder.encode(candidate).length;

        if (candidateBytes <= maxBytes) {
            low = mid + 1;
        } else {
            high = mid;
        }
    }

    const result = str.slice(0, Math.max(0, low - 1)) + '…';
    return result;
}

/**
 * Get byte length of string (UTF-8)
 * @param {string} str - String to measure
 * @returns {number} Byte length
 * @example byteLength('Hello') // 5
 */
export function byteLength(str) {
    if (!str) return 0;
    try {
        return new TextEncoder().encode(str).length;
    } catch (_) {
        // Fallback: approximate as character count
        return str.length;
    }
}

