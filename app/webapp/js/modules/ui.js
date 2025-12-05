/**
 * ui.js - Centralized UI State Management Module
 * RPG Methodology: Abstraction over DOM for managing UI states
 * @module modules/ui
 *
 * Purpose: Centralized control of all UI states (loading, error, success, idle)
 * Eliminates direct DOM manipulation scattered across codebase
 */

import * as dom from '../utils/dom.js';

/**
 * UI States
 * @enum {string}
 */
const UI_STATES = {
    IDLE: 'idle',
    LOADING: 'loading',
    ERROR: 'error',
    SUCCESS: 'success'
};

/**
 * UI Manager Class
 * Centralized state management for all UI components
 */
export class UI {
    constructor() {
        this._state = UI_STATES.IDLE;
        this._elements = this._cacheElements();
        this._initializeARIA();
    }

    /**
     * Cache DOM elements for performance
     * @private
     */
    _cacheElements() {
        return {
            loading: document.getElementById('loading'),
            error: document.getElementById('error'),
            resultCard: document.getElementById('resultCard'),
            shareBtn: document.getElementById('shareBtn'),
            calculateBtn: document.getElementById('calculateBtn'),
            form: document.getElementById('calculatorForm')
        };
    }

    /**
     * Initialize ARIA attributes for accessibility
     * @private
     */
    _initializeARIA() {
        if (this._elements.loading) {
            this._elements.loading.setAttribute('role', 'status');
            this._elements.loading.setAttribute('aria-live', 'polite');
        }
        if (this._elements.error) {
            this._elements.error.setAttribute('role', 'alert');
            this._elements.error.setAttribute('aria-live', 'assertive');
        }
        if (this._elements.resultCard) {
            this._elements.resultCard.setAttribute('role', 'region');
            this._elements.resultCard.setAttribute('aria-label', 'Результаты расчета');
        }
    }

    /**
     * Get current UI state (for debugging)
     * @returns {string} Current state
     */
    getState() {
        return this._state;
    }

    /**
     * Transition to new state
     * @private
     * @param {string} newState - New UI state
     */
    _setState(newState) {
        const oldState = this._state;
        this._state = newState;

        // Log state transitions (can be removed in production)
        if (oldState !== newState) {
            console.log(`UI state transition: ${oldState} → ${newState}`);
        }
    }

    /**
     * Show loading indicator
     * @param {string} [text='Рассчитываем стоимость...'] - Loading text
     */
    showLoading(text = 'Рассчитываем стоимость...') {
        this._setState(UI_STATES.LOADING);

        if (this._elements.loading) {
            this._elements.loading.textContent = text;
            this._fadeIn(this._elements.loading);
        }

        this.disableForm();
        this.hideError();
        this.hideResult();

        // Telegram Haptic Feedback
        this._hapticFeedback('light');
    }

    /**
     * Hide loading indicator
     */
    hideLoading() {
        if (this._elements.loading) {
            this._fadeOut(this._elements.loading);
        }

        this.enableForm();
    }

    /**
     * Show error message
     * @param {string} message - Error message to display
     */
    showError(message) {
        this._setState(UI_STATES.ERROR);

        if (this._elements.error) {
            this._elements.error.textContent = message;
            this._fadeIn(this._elements.error);

            // Focus on error for screen readers
            this._elements.error.setAttribute('tabindex', '-1');
            this._elements.error.focus();
        }

        this.hideLoading();
        this.hideResult();

        // Telegram Haptic Feedback
        this._hapticFeedback('heavy');
    }

    /**
     * Hide error message
     */
    hideError() {
        if (this._elements.error) {
            this._fadeOut(this._elements.error);
            this._elements.error.removeAttribute('tabindex');
        }
    }

    /**
     * Show result card
     */
    showResult() {
        this._setState(UI_STATES.SUCCESS);

        if (this._elements.resultCard) {
            dom.addClass(this._elements.resultCard, 'show');
        }

        this.hideLoading();
        this.hideError();
        this.showShareButton();

        // Scroll to result with smooth animation
        this.scrollToResult();

        // Telegram Haptic Feedback
        this._hapticFeedback('medium');
    }

    /**
     * Hide result card
     */
    hideResult() {
        if (this._elements.resultCard) {
            dom.removeClass(this._elements.resultCard, 'show');
        }

        this.hideShareButton();
    }

    /**
     * Show share button
     */
    showShareButton() {
        if (this._elements.shareBtn) {
            this._fadeIn(this._elements.shareBtn);
        }
    }

    /**
     * Hide share button
     */
    hideShareButton() {
        if (this._elements.shareBtn) {
            this._fadeOut(this._elements.shareBtn);
        }
    }

    /**
     * Scroll to result with smooth animation
     */
    scrollToResult() {
        if (this._elements.resultCard) {
            // Small delay to ensure the element is visible
            setTimeout(() => {
                this._elements.resultCard.scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest'
                });
            }, 100);
        }
    }

    /**
     * Disable form inputs and submit button
     */
    disableForm() {
        if (this._elements.calculateBtn) {
            this._elements.calculateBtn.disabled = true;
            this._elements.calculateBtn.setAttribute('aria-busy', 'true');
        }

        if (this._elements.form) {
            const inputs = this._elements.form.querySelectorAll('input, select, button');
            inputs.forEach(input => {
                input.disabled = true;
            });
        }
    }

    /**
     * Enable form inputs and submit button
     */
    enableForm() {
        if (this._elements.calculateBtn) {
            this._elements.calculateBtn.disabled = false;
            this._elements.calculateBtn.removeAttribute('aria-busy');
        }

        if (this._elements.form) {
            const inputs = this._elements.form.querySelectorAll('input, select, button');
            inputs.forEach(input => {
                input.disabled = false;
            });
        }
    }

    /**
     * Reset UI to idle state
     */
    reset() {
        this._setState(UI_STATES.IDLE);
        this.hideLoading();
        this.hideError();
        this.hideResult();
        this.enableForm();
    }

    /**
     * Fade in element with CSS transition
     * @private
     * @param {HTMLElement} element - Element to fade in
     */
    _fadeIn(element) {
        if (!element) return;

        element.style.display = 'block';
        element.style.opacity = '0';
        element.style.transition = 'opacity 0.3s ease-in-out';

        // Trigger reflow to ensure transition works
        void element.offsetHeight;

        element.style.opacity = '1';
    }

    /**
     * Fade out element with CSS transition
     * @private
     * @param {HTMLElement} element - Element to fade out
     */
    _fadeOut(element) {
        if (!element) return;

        element.style.opacity = '0';
        element.style.transition = 'opacity 0.3s ease-in-out';

        setTimeout(() => {
            element.style.display = 'none';
        }, 300);
    }

    /**
     * Trigger Telegram Haptic Feedback
     * @private
     * @param {string} type - Haptic type: 'light', 'medium', 'heavy'
     */
    _hapticFeedback(type = 'medium') {
        try {
            const tg = window.Telegram?.WebApp;
            if (tg && tg.HapticFeedback) {
                switch (type) {
                    case 'light':
                        tg.HapticFeedback.impactOccurred('light');
                        break;
                    case 'medium':
                        tg.HapticFeedback.impactOccurred('medium');
                        break;
                    case 'heavy':
                        tg.HapticFeedback.impactOccurred('heavy');
                        break;
                    default:
                        tg.HapticFeedback.impactOccurred('medium');
                }
            }
        } catch (e) {
            // Haptic feedback is optional, silently fail
            console.debug('Haptic feedback not available:', e);
        }
    }

    /**
     * Show toast notification
     * @param {string} message - Toast message
     * @param {string} [type='info'] - Toast type: 'info', 'success', 'error', 'warning'
     * @param {number} [duration=3000] - Duration in milliseconds
     */
    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toast.setAttribute('role', 'status');
        toast.setAttribute('aria-live', 'polite');

        // Toast styles
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };

        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: ${colors[type] || colors.info};
            color: #fff;
            padding: 12px 24px;
            border-radius: 8px;
            z-index: 1000;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            font-size: 14px;
            font-weight: 500;
            max-width: 90%;
            text-align: center;
            animation: slideUp 0.3s ease-out;
        `;

        document.body.appendChild(toast);

        // Auto remove after duration
        setTimeout(() => {
            toast.style.animation = 'slideDown 0.3s ease-in';
            setTimeout(() => toast.remove(), 300);
        }, duration);

        // Haptic feedback for toast
        if (type === 'error') {
            this._hapticFeedback('heavy');
        } else if (type === 'success') {
            this._hapticFeedback('medium');
        } else {
            this._hapticFeedback('light');
        }
    }
}

// Export singleton instance
export const ui = new UI();

// Export UI_STATES for external use if needed
export { UI_STATES };

