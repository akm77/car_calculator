/**
 * hints.js - Visual Hints System Module
 * MVP Implementation - Sprint 2025-12-08
 */

function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

export class HintsManager {
    constructor(constants, messages) {
        this.constants = constants;
        this.messages = messages;
        this.activeTooltips = new Map();
    }

    getAgeHintData(year) {
        const yearNum = parseInt(year);
        if (isNaN(yearNum) || yearNum < 1990) {
            return null;
        }

        const currentYear = new Date().getFullYear();
        const age = currentYear - yearNum;

        const { AGE } = this.constants.HINT_THRESHOLDS;
        const { age: messages } = this.messages.hints;

        if (age >= AGE.OPTIMAL_MIN && age <= AGE.OPTIMAL_MAX) {
            return {
                zone: 'optimal',
                className: 'input-hint-optimal',
                text: messages.optimal,
                ariaLabel: 'Оптимальный возраст'
            };
        }

        if (age < AGE.OPTIMAL_MIN) {
            return {
                zone: 'prohibitive',
                className: 'input-hint-prohibitive',
                text: messages.new_expensive,
                ariaLabel: 'Высокая пошлина'
            };
        }

        if (age > AGE.OPTIMAL_MAX) {
            return {
                zone: 'warning',
                className: 'input-hint-warning',
                text: messages.old_expensive,
                ariaLabel: 'Пошлина выше оптимальной'
            };
        }

        return {
            zone: 'acceptable',
            className: 'input-hint-acceptable',
            text: messages.acceptable,
            ariaLabel: 'Приемлемый возраст'
        };
    }

    getPowerHintData(powerHp) {
        const power = parseInt(powerHp);
        if (isNaN(power) || power <= 0) {
            return null;
        }

        const { POWER } = this.constants.HINT_THRESHOLDS;
        const { power: messages } = this.messages.hints;

        if (power <= POWER.OPTIMAL_MAX) {
            return {
                zone: 'optimal',
                className: 'input-hint-optimal',
                text: messages.optimal,
                ariaLabel: 'Минимальный утильсбор'
            };
        }

        if (power <= POWER.ACCEPTABLE_MAX) {
            return {
                zone: 'acceptable',
                className: 'input-hint-acceptable',
                text: messages.acceptable,
                ariaLabel: 'Утильсбор начинает расти'
            };
        }

        if (power <= POWER.WARNING_MAX) {
            return {
                zone: 'warning',
                className: 'input-hint-warning',
                text: messages.warning,
                ariaLabel: 'Высокий утильсбор'
            };
        }

        return {
            zone: 'prohibitive',
            className: 'input-hint-prohibitive',
            text: messages.prohibitive,
            ariaLabel: 'Запретительный утильсбор'
        };
    }

    applyHintToField(fieldElement, hintData) {
        if (!fieldElement) return;

        const hintClasses = [
            'input-hint-optimal',
            'input-hint-acceptable',
            'input-hint-warning',
            'input-hint-prohibitive'
        ];
        fieldElement.classList.remove(...hintClasses);

        if (hintData && hintData.className) {
            fieldElement.classList.add(hintData.className);
            fieldElement.setAttribute('aria-describedby', fieldElement.id + '-hint');
            if (hintData.ariaLabel) {
                fieldElement.setAttribute('aria-label', hintData.ariaLabel);
            }
        } else {
            fieldElement.removeAttribute('aria-describedby');
            fieldElement.removeAttribute('aria-label');
        }
    }

    showHintText(fieldElement, text) {
        if (!fieldElement || !text) return;

        this.hideHintText(fieldElement);

        const hintTextEl = document.createElement('div');
        hintTextEl.className = 'hint-text';
        hintTextEl.id = fieldElement.id + '-hint';
        hintTextEl.textContent = text;
        hintTextEl.setAttribute('role', 'status');
        hintTextEl.setAttribute('aria-live', 'polite');

        fieldElement.insertAdjacentElement('afterend', hintTextEl);
    }

    hideHintText(fieldElement) {
        if (!fieldElement) return;

        const existingHint = fieldElement.nextElementSibling;
        if (existingHint && existingHint.classList.contains('hint-text')) {
            existingHint.remove();
        }
    }

    _createTooltip(tooltipText, iconElement) {
        const tooltip = document.createElement('div');
        tooltip.className = 'hint-tooltip';
        tooltip.textContent = tooltipText;
        tooltip.setAttribute('role', 'tooltip');

        const iconRect = iconElement.getBoundingClientRect();
        const scrollY = window.scrollY || window.pageYOffset;
        const scrollX = window.scrollX || window.pageXOffset;

        tooltip.style.position = 'absolute';
        tooltip.style.left = iconRect.left + scrollX + 'px';
        tooltip.style.top = iconRect.bottom + scrollY + 8 + 'px';
        tooltip.classList.add('tooltip-bottom');

        document.body.appendChild(tooltip);
        const tooltipRect = tooltip.getBoundingClientRect();

        if (tooltipRect.right > window.innerWidth - 10) {
            tooltip.style.left = window.innerWidth - tooltipRect.width - 20 + scrollX + 'px';
        }

        if (tooltipRect.bottom > window.innerHeight - 10) {
            tooltip.style.top = iconRect.top + scrollY - tooltipRect.height - 8 + 'px';
            tooltip.classList.remove('tooltip-bottom');
            tooltip.classList.add('tooltip-top');
        }

        return tooltip;
    }

    showTooltip(iconElement, tooltipText) {
        if (!iconElement || !tooltipText) return;

        this.hideTooltip(iconElement);

        const tooltip = this._createTooltip(tooltipText, iconElement);
        this.activeTooltips.set(iconElement, tooltip);

        setTimeout(() => {
            this.hideTooltip(iconElement);
        }, 5000);
    }

    hideTooltip(iconElement) {
        const tooltip = this.activeTooltips.get(iconElement);
        if (tooltip) {
            tooltip.remove();
            this.activeTooltips.delete(iconElement);
        }
    }

    initTooltips() {
        const fields = [
            {
                fieldId: 'year',
                labelText: 'Год выпуска',
                tooltipText: this.messages.hints.age.tooltip
            },
            {
                fieldId: 'enginePowerHp',
                labelText: 'Мощность двигателя',
                tooltipText: this.messages.hints.power.tooltip
            }
        ];

        fields.forEach(({ fieldId, labelText, tooltipText }) => {
            const label = document.querySelector('label[for="' + fieldId + '"]');
            if (!label) return;

            if (label.querySelector('.info-icon')) return;

            const infoIcon = document.createElement('span');
            infoIcon.className = 'info-icon';
            infoIcon.setAttribute('role', 'button');
            infoIcon.setAttribute('tabindex', '0');
            infoIcon.setAttribute('aria-label', 'Информация о поле "' + labelText + '"');

            label.classList.add('has-info-icon');
            label.appendChild(infoIcon);

            const handleShowTooltip = (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.showTooltip(infoIcon, tooltipText);
            };

            const handleHideTooltip = () => {
                this.hideTooltip(infoIcon);
            };

            infoIcon.addEventListener('click', handleShowTooltip);

            infoIcon.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    handleShowTooltip(e);
                }
            });

            infoIcon.addEventListener('mouseenter', handleShowTooltip);
            infoIcon.addEventListener('mouseleave', handleHideTooltip);

            document.addEventListener('click', (e) => {
                if (!infoIcon.contains(e.target)) {
                    this.hideTooltip(infoIcon);
                }
            });
        });
    }

    attachFieldHints(fieldElement, fieldType) {
        if (!fieldElement) return;

        const getHintData = fieldType === 'age'
            ? this.getAgeHintData.bind(this)
            : this.getPowerHintData.bind(this);

        const handleInput = debounce((e) => {
            const value = e.target.value;
            const hintData = getHintData(value);

            this.applyHintToField(fieldElement, hintData);

            if (hintData && hintData.text) {
                this.showHintText(fieldElement, hintData.text);
            } else {
                this.hideHintText(fieldElement);
            }
        }, 300);

        fieldElement.addEventListener('input', handleInput);

        fieldElement.addEventListener('blur', (e) => {
            if (!e.target.value) {
                this.applyHintToField(fieldElement, null);
                this.hideHintText(fieldElement);
            }
        });
    }

    init() {
        this.initTooltips();

        const yearField = document.getElementById('year');
        if (yearField) {
            this.attachFieldHints(yearField, 'age');
        }

        const powerField = document.getElementById('enginePowerHp');
        if (powerField) {
            this.attachFieldHints(powerField, 'power');
        }
    }

    destroy() {
        this.activeTooltips.forEach((tooltip) => tooltip.remove());
        this.activeTooltips.clear();

        const hintTexts = document.querySelectorAll('.hint-text');
        hintTexts.forEach(el => el.remove());

        const fields = [
            document.getElementById('year'),
            document.getElementById('enginePowerHp')
        ];
        fields.forEach(field => {
            if (field) {
                this.applyHintToField(field, null);
            }
        });
    }
}
