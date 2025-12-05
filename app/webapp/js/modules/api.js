/**
 * API Client Module
 * Robust HTTP client with retry, timeout, and improved error handling
 *
 * Features:
 * - Exponential backoff retry on network errors
 * - Configurable timeout with AbortController
 * - Custom error types (NetworkError, TimeoutError, ValidationError)
 * - FastAPI error response parsing
 * - Structured logging with timestamps
 *
 * Dependencies: constants.js (API_CONFIG, API_ENDPOINTS)
 */

import { API_CONFIG, API_ENDPOINTS } from '../config/constants.js';

/**
 * Custom API Error class
 * Extends Error with additional context (status, code, timestamp)
 */
export class APIError extends Error {
    /**
     * @param {string} message - Error message
     * @param {number|null} status - HTTP status code (null for network errors)
     * @param {string} code - Error code (NetworkError, TimeoutError, ValidationError, ServerError)
     * @param {object|null} details - Additional error details from server
     */
    constructor(message, status = null, code = 'UnknownError', details = null) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.code = code;
        this.details = details;
        this.timestamp = new Date().toISOString();
    }

    /**
     * Check if error is a network error (no response from server)
     */
    isNetworkError() {
        return this.code === 'NetworkError';
    }

    /**
     * Check if error is a timeout error
     */
    isTimeoutError() {
        return this.code === 'TimeoutError';
    }

    /**
     * Check if error is a validation error (4xx)
     */
    isValidationError() {
        return this.code === 'ValidationError' || (this.status >= 400 && this.status < 500);
    }

    /**
     * Check if error is a server error (5xx)
     */
    isServerError() {
        return this.code === 'ServerError' || (this.status >= 500 && this.status < 600);
    }

    /**
     * Get user-friendly error message
     */
    getUserMessage() {
        if (this.isNetworkError()) {
            return 'Нет соединения с сервером. Проверьте интернет-соединение.';
        }
        if (this.isTimeoutError()) {
            return 'Превышено время ожидания. Попробуйте еще раз.';
        }
        if (this.isValidationError()) {
            // Use server message for validation errors
            return this.message || 'Ошибка валидации данных.';
        }
        if (this.isServerError()) {
            return 'Ошибка сервера. Попробуйте позже.';
        }
        return this.message || 'Произошла ошибка при выполнении запроса.';
    }

    /**
     * Convert error to log-friendly format
     */
    toLogFormat() {
        return {
            name: this.name,
            message: this.message,
            code: this.code,
            status: this.status,
            details: this.details,
            timestamp: this.timestamp,
        };
    }
}

/**
 * API Client
 * Handles all HTTP requests with retry logic, timeout, and error handling
 */
export class APIClient {
    /**
     * @param {object} options - Configuration options
     * @param {string} options.baseURL - Base URL for API (auto-detected if not provided)
     * @param {number} options.timeout - Request timeout in milliseconds
     * @param {number} options.maxRetries - Maximum retry attempts
     * @param {number} options.retryDelay - Initial retry delay in milliseconds
     * @param {string} options.csrfToken - CSRF token (generated if not provided)
     */
    constructor(options = {}) {
        this.baseURL = options.baseURL || this.resolveBaseURL();
        this.timeout = options.timeout || API_CONFIG.TIMEOUT;
        this.maxRetries = options.maxRetries || API_CONFIG.RETRY_COUNT;
        this.retryDelay = options.retryDelay || API_CONFIG.RETRY_DELAY;
        this.csrfToken = options.csrfToken || this.generateCSRFToken();

        console.log(`[APIClient] Initialized with baseURL: ${this.baseURL}, timeout: ${this.timeout}ms, maxRetries: ${this.maxRetries}`);
    }

    /**
     * Auto-detect base URL from current location
     * Priority: ?api_base query param > current host > fallback
     */
    resolveBaseURL() {
        try {
            const params = new URLSearchParams(location.search);
            const override = params.get('api_base');
            if (override) return override.replace(/\/$/, '');

            if (location.protocol === 'https:' || location.protocol === 'http:') {
                const currentHost = location.host;
                if (currentHost.includes('ngrok') || !currentHost.includes('localhost')) {
                    return `${location.protocol}//${currentHost}`;
                }
                return `${location.protocol}//${location.host}`;
            }
            return window.location.hostname ? `https://${window.location.hostname}` : '';
        } catch (error) {
            console.warn('[APIClient] Failed to resolve base URL:', error);
            return '';
        }
    }

    /**
     * Generate CSRF token for security
     */
    generateCSRFToken() {
        return 'csrf_' + Math.random().toString(36).substr(2, 15);
    }

    /**
     * Build full URL from path
     * @param {string} path - API endpoint path
     * @returns {string} Full URL
     */
    getURL(path) {
        if (path.startsWith('http')) return path;
        if (this.baseURL) return this.baseURL + path;
        return path;
    }

    /**
     * Get default headers for requests
     * @returns {object} Headers object
     */
    getDefaultHeaders() {
        return {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'ngrok-skip-browser-warning': 'true',
            'User-Agent': 'Mozilla/5.0 (compatible; TelegramWebApp)',
            'Accept': 'application/json, text/plain, */*',
            'Cache-Control': 'no-cache',
            ...(this.csrfToken && { 'X-CSRF-Token': this.csrfToken }),
        };
    }

    /**
     * Fetch with timeout using AbortController
     * @param {string} url - Request URL
     * @param {object} options - Fetch options
     * @param {number} timeout - Timeout in milliseconds
     * @returns {Promise<Response>} Fetch response
     * @throws {APIError} Timeout error (code: TimeoutError, status: 408)
     */
    async fetchWithTimeout(url, options = {}, timeout = this.timeout) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const fetchOptions = {
            ...options,
            signal: controller.signal,
            headers: {
                ...this.getDefaultHeaders(),
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, fetchOptions);
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);

            // Check if error is due to abort (timeout)
            if (error.name === 'AbortError') {
                throw new APIError(
                    `Request timeout after ${timeout}ms`,
                    408,
                    'TimeoutError',
                    { url, timeout }
                );
            }

            // Other errors (network, CORS, etc.)
            throw error;
        }
    }

    /**
     * Fetch with retry logic (exponential backoff)
     * Only retries on network errors, not on 4xx/5xx responses
     *
     * @param {string} url - Request URL
     * @param {object} options - Fetch options
     * @param {number} maxRetries - Maximum retry attempts
     * @returns {Promise<Response>} Fetch response
     * @throws {APIError} Network error or HTTP error
     */
    async fetchWithRetry(url, options = {}, maxRetries = this.maxRetries) {
        let lastError;

        for (let attempt = 0; attempt < maxRetries; attempt++) {
            try {
                const response = await this.fetchWithTimeout(url, options);

                // HTTP errors (4xx, 5xx) - don't retry, throw immediately
                if (!response.ok) {
                    const errorData = await this.parseErrorResponse(response);
                    throw this.createHTTPError(response.status, errorData);
                }

                // Success
                if (attempt > 0) {
                    console.log(`[APIClient] Request succeeded on attempt ${attempt + 1}`);
                }
                return response;

            } catch (error) {
                lastError = error;

                // Don't retry on HTTP errors (4xx, 5xx) or timeout errors
                if (error instanceof APIError && !error.isNetworkError()) {
                    throw error;
                }

                // Log retry attempt
                const attemptNum = attempt + 1;
                if (attemptNum < maxRetries) {
                    const delay = this.retryDelay * Math.pow(2, attempt);
                    console.warn(`[APIClient] Attempt ${attemptNum} failed: ${error.message}. Retrying in ${delay}ms...`);
                    await this.delay(delay);
                } else {
                    console.error(`[APIClient] All ${maxRetries} attempts failed`);
                }
            }
        }

        // All retries exhausted
        if (lastError instanceof APIError) {
            throw lastError;
        }

        // Wrap unknown errors
        throw new APIError(
            lastError.message || 'Network request failed',
            null,
            'NetworkError',
            { originalError: lastError.toString() }
        );
    }

    /**
     * Parse error response from FastAPI
     * Handles both JSON {"detail": "..."} and plain text responses
     *
     * @param {Response} response - Fetch response
     * @returns {Promise<object>} Parsed error data
     */
    async parseErrorResponse(response) {
        try {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                // FastAPI returns {"detail": "error message"} or {"detail": [{...}]} for validation
                if (data.detail) {
                    if (typeof data.detail === 'string') {
                        return { message: data.detail };
                    } else if (Array.isArray(data.detail)) {
                        // Pydantic validation errors
                        const errors = data.detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join(', ');
                        return { message: errors, details: data.detail };
                    }
                }
                return data;
            } else {
                const text = await response.text();
                return { message: text || response.statusText };
            }
        } catch (error) {
            return { message: response.statusText || 'Unknown error' };
        }
    }

    /**
     * Create APIError from HTTP response
     * @param {number} status - HTTP status code
     * @param {object} errorData - Parsed error data
     * @returns {APIError} API error instance
     */
    createHTTPError(status, errorData) {
        let code = 'ServerError';
        if (status >= 400 && status < 500) {
            code = 'ValidationError';
        } else if (status >= 500) {
            code = 'ServerError';
        }

        const message = errorData.message || `HTTP ${status} error`;
        const details = errorData.details || null;

        return new APIError(message, status, code, details);
    }

    /**
     * Delay helper for retry logic
     * @param {number} ms - Delay in milliseconds
     * @returns {Promise<void>}
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Generic GET request
     * @param {string} path - API endpoint path
     * @param {object} options - Additional fetch options
     * @returns {Promise<any>} Parsed JSON response
     */
    async get(path, options = {}) {
        const url = this.getURL(path);
        console.log(`[APIClient] GET ${url}`);

        try {
            const response = await this.fetchWithRetry(url, {
                method: 'GET',
                ...options,
            });

            return await response.json();
        } catch (error) {
            this.logError('GET', path, error);
            throw error;
        }
    }

    /**
     * Generic POST request
     * @param {string} path - API endpoint path
     * @param {object} data - Request body data
     * @param {object} options - Additional fetch options
     * @returns {Promise<any>} Parsed JSON response
     */
    async post(path, data, options = {}) {
        const url = this.getURL(path);
        console.log(`[APIClient] POST ${url}`, data);

        try {
            const response = await this.fetchWithRetry(url, {
                method: 'POST',
                body: JSON.stringify(data),
                ...options,
            });

            return await response.json();
        } catch (error) {
            this.logError('POST', path, error);
            throw error;
        }
    }

    /**
     * Log error in structured format
     * @param {string} method - HTTP method
     * @param {string} path - API endpoint path
     * @param {Error} error - Error object
     */
    logError(method, path, error) {
        if (error instanceof APIError) {
            console.error(`[APIClient] ${method} ${path} failed:`, error.toLogFormat());
        } else {
            console.error(`[APIClient] ${method} ${path} failed:`, {
                message: error.message,
                timestamp: new Date().toISOString(),
            });
        }
    }

    // =====================================================================
    // Specific API methods for car_calculator
    // =====================================================================

    /**
     * Calculate car import cost
     * @param {object} formData - Calculation form data
     * @returns {Promise<object>} Calculation result
     */
    async calculate(formData) {
        return this.post(API_ENDPOINTS.CALCULATE, formData);
    }

    /**
     * Get metadata (countries, freight types, etc.)
     * @returns {Promise<object>} Metadata
     */
    async getMeta() {
        return this.get(API_ENDPOINTS.META);
    }

    /**
     * Get current exchange rates
     * @returns {Promise<object>} Exchange rates
     */
    async getRates() {
        return this.get(API_ENDPOINTS.RATES);
    }

    /**
     * Refresh exchange rates from CBR
     * @returns {Promise<object>} Updated exchange rates
     */
    async refreshRates() {
        return this.post(API_ENDPOINTS.REFRESH_RATES, {});
    }

    /**
     * Health check
     * @returns {Promise<object>} Health status
     */
    async health() {
        return this.get(API_ENDPOINTS.HEALTH);
    }
}

/**
 * Create and export singleton instance
 * Can be replaced with custom configuration if needed
 */
export const api = new APIClient();

// Export for testing/debugging
if (typeof window !== 'undefined') {
    window.APIClient = APIClient;
    window.APIError = APIError;
}

