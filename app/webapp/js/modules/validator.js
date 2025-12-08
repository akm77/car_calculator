/**
 * Form Validator Module
 * Single source of truth for form validation rules
 * Synchronized with backend constraints (app/calculation/models.py)
 *
 * @module validator
 */

import { Constraints } from '../config/constants.js';
import { Messages } from '../config/messages.js';

/**
 * FormValidator Class
 * Provides comprehensive form validation with support for:
 * - Full form validation
 * - Individual field validation (for real-time feedback)
 * - Custom validators
 * - Field constraints inspection
 */
export class FormValidator {
    /**
     * @param {Object} constraints - Validation constraints (defaults to Constraints from constants.js)
     */
    constructor(constraints = Constraints) {
        this.constraints = constraints;
        this.customValidators = new Map(); // fieldName -> validator function
    }

    /**
     * Validate entire form data
     * @param {FormData|Object} formData - Form data to validate
     * @returns {{isValid: boolean, errors: Array<{field: string, message: string}>}}
     */
    validate(formData) {
        const errors = [];

        // Convert FormData to object if needed
        const data = formData instanceof FormData
            ? Object.fromEntries(formData.entries())
            : formData;

        // Validate year
        const yearError = this.validateField('year', data.year);
        if (yearError) {
            errors.push({ field: 'year', message: yearError });
        }

        // Validate engine_cc
        const engineError = this.validateField('engine_cc', data.engineCc || data.engine_cc);
        if (engineError) {
            errors.push({ field: 'engine_cc', message: engineError });
        }

        // NEW 2025: Validate engine_power_hp
        const enginePowerError = this.validateField('engine_power_hp', data.enginePowerHp || data.engine_power_hp);
        if (enginePowerError) {
            errors.push({ field: 'engine_power_hp', message: enginePowerError });
        }

        // Validate purchase_price
        const priceError = this.validateField('purchase_price', data.purchasePrice || data.purchase_price);
        if (priceError) {
            errors.push({ field: 'purchase_price', message: priceError });
        }

        // Validate country (must not be empty)
        const countryError = this.validateField('country', data.country);
        if (countryError) {
            errors.push({ field: 'country', message: countryError });
        }

        // Run custom validators
        for (const [fieldName, validator] of this.customValidators) {
            const value = data[fieldName];
            const error = validator(value, data);
            if (error) {
                errors.push({ field: fieldName, message: error });
            }
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Validate individual field (for real-time validation)
     * @param {string} name - Field name (year, engine_cc, purchase_price, country)
     * @param {*} value - Field value
     * @returns {string|null} - Error message or null if valid
     */
    validateField(name, value) {
        // Check custom validators first
        if (this.customValidators.has(name)) {
            const customError = this.customValidators.get(name)(value);
            if (customError) return customError;
        }

        // Built-in validators
        switch(name) {
            case 'year': {
                const year = parseInt(value);
                if (isNaN(year)) {
                    return Messages.errors.INVALID_YEAR_FORMAT || 'Неверный формат года';
                }

                const maxYear = typeof this.constraints.YEAR_MAX === 'function'
                    ? this.constraints.YEAR_MAX()
                    : this.constraints.YEAR_MAX;

                if (year > maxYear) {
                    return Messages.errors.INVALID_YEAR_FUTURE;
                }
                if (year < this.constraints.YEAR_MIN) {
                    return Messages.errors.INVALID_YEAR_OLD;
                }
                break;
            }

            case 'engine_cc':
            case 'engineCc': {
                const cc = parseInt(value);
                if (isNaN(cc)) {
                    return Messages.errors.INVALID_ENGINE_FORMAT || 'Неверный формат объема двигателя';
                }
                if (cc < this.constraints.ENGINE_CC_MIN || cc > this.constraints.ENGINE_CC_MAX) {
                    return Messages.errors.INVALID_ENGINE_RANGE ||
                           `Объем двигателя должен быть от ${this.constraints.ENGINE_CC_MIN} до ${this.constraints.ENGINE_CC_MAX} см³`;
                }
                break;
            }

            // NEW 2025: Engine power validation
            case 'engine_power_hp':
            case 'enginePowerHp': {
                const power = parseInt(value, 10);

                if (isNaN(power)) {
                    return Messages.errors.enginePowerHpRequired || 'Введите мощность двигателя в л.с.';
                }

                if (power < this.constraints.ENGINE_POWER_HP_MIN) {
                    return `Минимальная мощность: ${this.constraints.ENGINE_POWER_HP_MIN} л.с.`;
                }

                if (power > this.constraints.ENGINE_POWER_HP_MAX) {
                    return `Максимальная мощность: ${this.constraints.ENGINE_POWER_HP_MAX} л.с.`;
                }

                return null; // validation passed
            }

            case 'purchase_price':
            case 'purchasePrice': {
                const price = parseFloat(value);
                if (isNaN(price)) {
                    return Messages.errors.INVALID_PRICE_FORMAT || 'Неверный формат цены';
                }
                if (price <= 0) {
                    return Messages.errors.INVALID_PRICE;
                }
                break;
            }

            case 'country': {
                if (!value || value.trim() === '') {
                    return Messages.errors.NO_COUNTRY || 'Пожалуйста, выберите страну покупки';
                }
                break;
            }

            default:
                // Unknown field - no validation
                return null;
        }

        return null; // No errors
    }

    /**
     * Get field constraints for UI hints (min, max, pattern, etc.)
     * @param {string} name - Field name
     * @returns {{min?: number, max?: number, pattern?: string, step?: number}|null}
     */
    getFieldConstraints(name) {
        switch(name) {
            case 'year':
                return {
                    min: this.constraints.YEAR_MIN,
                    max: typeof this.constraints.YEAR_MAX === 'function'
                        ? this.constraints.YEAR_MAX()
                        : this.constraints.YEAR_MAX,
                    step: 1
                };

            case 'engine_cc':
            case 'engineCc':
                return {
                    min: this.constraints.ENGINE_CC_MIN,
                    max: this.constraints.ENGINE_CC_MAX,
                    step: this.constraints.ENGINE_CC_STEP || 50
                };

            case 'engine_power_hp':
            case 'enginePowerHp':
                return {
                    min: this.constraints.ENGINE_POWER_HP_MIN,
                    max: this.constraints.ENGINE_POWER_HP_MAX,
                    step: 1,
                    required: true,
                    type: 'number'
                };

            case 'purchase_price':
            case 'purchasePrice':
                return {
                    min: this.constraints.PRICE_MIN,
                    step: this.constraints.PRICE_STEP || 0.01
                };

            default:
                return null;
        }
    }

    /**
     * Add custom validator for a field
     * Custom validators are called BEFORE built-in validators
     *
     * @param {string} fieldName - Field name to validate
     * @param {Function} validatorFn - Validator function: (value, allFormData?) => errorMessage | null
     * @returns {FormValidator} - this (for chaining)
     *
     * @example
     * validator.addCustomValidator('year', (value) => {
     *     const year = parseInt(value);
     *     if (year === 2020) return 'Автомобили 2020 года временно не принимаются';
     *     return null;
     * });
     */
    addCustomValidator(fieldName, validatorFn) {
        if (typeof validatorFn !== 'function') {
            throw new Error('Validator must be a function');
        }
        this.customValidators.set(fieldName, validatorFn);
        return this; // Allow chaining
    }

    /**
     * Remove custom validator
     * @param {string} fieldName - Field name
     * @returns {boolean} - true if validator was removed
     */
    removeCustomValidator(fieldName) {
        return this.customValidators.delete(fieldName);
    }

    /**
     * Clear all custom validators
     */
    clearCustomValidators() {
        this.customValidators.clear();
    }

    /**
     * Check if field has custom validator
     * @param {string} fieldName - Field name
     * @returns {boolean}
     */
    hasCustomValidator(fieldName) {
        return this.customValidators.has(fieldName);
    }
}

/**
 * Create default validator instance
 * @returns {FormValidator}
 */
export function createValidator() {
    return new FormValidator();
}

// Export default instance for convenience
export const validator = createValidator();

