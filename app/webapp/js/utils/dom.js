/**
 * dom.js - Pure DOM manipulation utilities
 * RPG Methodology: Simple helpers without framework overhead
 * @module utils/dom
 */

/**
 * Show element by adding 'show' class
 * @param {string|HTMLElement} element - Element ID or DOM node
 */
export function show(element) {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (el) {
        el.classList.add('show');
    }
}

/**
 * Hide element by removing 'show' class
 * @param {string|HTMLElement} element - Element ID or DOM node
 */
export function hide(element) {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (el) {
        el.classList.remove('show');
    }
}

/**
 * Set innerHTML of element
 * @param {string|HTMLElement} element - Element ID or DOM node
 * @param {string} html - HTML content
 */
export function setContent(element, html) {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (el) {
        el.innerHTML = html;
    }
}

/**
 * Set textContent of element (safe, no XSS)
 * @param {string|HTMLElement} element - Element ID or DOM node
 * @param {string} text - Text content
 */
export function setText(element, text) {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (el) {
        el.textContent = text;
    }
}

/**
 * Toggle element visibility
 * @param {string|HTMLElement} element - Element ID or DOM node
 * @param {boolean} [force] - Force show (true) or hide (false)
 */
export function toggle(element, force) {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (el) {
        if (force === undefined) {
            el.classList.toggle('show');
        } else if (force) {
            el.classList.add('show');
        } else {
            el.classList.remove('show');
        }
    }
}

/**
 * Set display style (block/none)
 * @param {string|HTMLElement} element - Element ID or DOM node
 * @param {string} display - Display value ('block', 'none', 'flex', etc.)
 */
export function setDisplay(element, display) {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (el) {
        el.style.display = display;
    }
}

/**
 * Add CSS class to element
 * @param {string|HTMLElement} element - Element ID or DOM node
 * @param {string} className - Class name to add
 */
export function addClass(element, className) {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (el) {
        el.classList.add(className);
    }
}

/**
 * Remove CSS class from element
 * @param {string|HTMLElement} element - Element ID or DOM node
 * @param {string} className - Class name to remove
 */
export function removeClass(element, className) {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (el) {
        el.classList.remove(className);
    }
}

/**
 * Check if element has class
 * @param {string|HTMLElement} element - Element ID or DOM node
 * @param {string} className - Class name to check
 * @returns {boolean} True if element has class
 */
export function hasClass(element, className) {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    return el ? el.classList.contains(className) : false;
}

/**
 * Get element by ID (shorthand)
 * @param {string} id - Element ID
 * @returns {HTMLElement|null} Element or null
 */
export function getEl(id) {
    return document.getElementById(id);
}

/**
 * Query selector (shorthand)
 * @param {string} selector - CSS selector
 * @param {HTMLElement} [parent=document] - Parent element
 * @returns {HTMLElement|null} First matching element or null
 */
export function query(selector, parent = document) {
    return parent.querySelector(selector);
}

/**
 * Query all selector (shorthand)
 * @param {string} selector - CSS selector
 * @param {HTMLElement} [parent=document] - Parent element
 * @returns {NodeList} All matching elements
 */
export function queryAll(selector, parent = document) {
    return parent.querySelectorAll(selector);
}

/**
 * Debounce function - delays execution until after wait time
 * @param {Function} fn - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 * @example const debouncedSearch = debounce(search, 300);
 */
export function debounce(fn, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn.apply(this, args), delay);
    };
}

/**
 * Throttle function - limits execution to once per time period
 * @param {Function} fn - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
export function throttle(fn, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            fn.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Create element with properties
 * @param {string} tag - HTML tag name
 * @param {Object} [props={}] - Properties (className, id, textContent, etc.)
 * @param {Array<HTMLElement>} [children=[]] - Child elements
 * @returns {HTMLElement} Created element
 * @example createElement('div', {className: 'card', id: 'myCard'}, [childEl])
 */
export function createElement(tag, props = {}, children = []) {
    const el = document.createElement(tag);

    // Set properties
    Object.keys(props).forEach(key => {
        if (key === 'className') {
            el.className = props[key];
        } else if (key === 'textContent') {
            el.textContent = props[key];
        } else if (key === 'innerHTML') {
            el.innerHTML = props[key];
        } else {
            el[key] = props[key];
        }
    });

    // Append children
    children.forEach(child => {
        if (child) el.appendChild(child);
    });

    return el;
}

/**
 * Remove all children from element
 * @param {string|HTMLElement} element - Element ID or DOM node
 */
export function clearChildren(element) {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (el) {
        el.innerHTML = '';
    }
}

/**
 * Scroll element into view smoothly
 * @param {string|HTMLElement} element - Element ID or DOM node
 * @param {Object} [options] - Scroll options
 */
export function scrollToElement(element, options = { behavior: 'smooth', block: 'start' }) {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (el && el.scrollIntoView) {
        el.scrollIntoView(options);
    }
}

