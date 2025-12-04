/**
 * Messages Configuration
 * Single source of truth for all user-facing text in the WebApp
 * Synchronized with backend messages (app/core/messages.py)
 */

export const Messages = {
    // Error messages (validation and API errors)
    errors: {
        NO_COUNTRY: 'Пожалуйста, выберите страну покупки',
        INVALID_YEAR_FUTURE: 'Год выпуска не может быть больше текущего',
        INVALID_YEAR_OLD: 'Год выпуска должен быть не менее 1990',
        INVALID_ENGINE_RANGE: 'Объем двигателя должен быть от 500 до 10000 см³',
        INVALID_PRICE: 'Цена покупки должна быть больше 0',
        CALCULATION_ERROR: 'Ошибка расчета',
        NETWORK_ERROR: 'Ошибка сети. Проверьте подключение',
        SEND_FAILED: 'Не удалось отправить в чат',
        COPY_FAILED: 'Не удалось скопировать',
        TELEGRAM_SEND_ERROR: 'Ошибка отправки в Telegram',
        SEND_DATA_FAILED: 'Ошибка отправки данных',
    },

    // Button labels
    buttons: {
        CALCULATE: 'Рассчитать стоимость',
        BACK: '↩️ Вернуться к расчётам',
        SHARE: '📤 Поделиться результатом',
        LOADING: 'Производится расчёт...',
        TAB_CALC: 'Расчёт',
        TAB_RESULT: 'Результат',
    },

    // Field labels
    labels: {
        COUNTRY: 'Страна покупки',
        YEAR: 'Год выпуска',
        ENGINE: 'Объем двигателя',
        PRICE: 'Цена покупки',
        VEHICLE_TYPE: 'Тип транспортного средства',
        FREIGHT_TYPE: 'Тип фрахта',
        TOTAL: 'ИТОГО',
        CUSTOMS_VALUE: 'Таможенная стоимость',
        DUTY: 'Пошлина',
        DUTY_RATE: 'Ставка пошлины',
        MIN_RATE: 'Мин. ставка',
        AGE: 'Возраст авто',
        TOTAL_COST: 'Общая стоимость',
        BREAKDOWN: 'Детализация',
    },

    // Breakdown item labels (cost components)
    breakdown: {
        PURCHASE_PRICE: 'Закупочная стоимость',
        COUNTRY_EXPENSES: 'Расходы в стране',
        FREIGHT: 'Фрахт',
        DUTIES: 'Таможенная пошлина',
        CUSTOMS_SERVICES: 'Таможенное оформление',
        UTILIZATION_FEE: 'Утилизационный сбор',
        ERA_GLONASS: 'Эра-Глонасс',
        COMPANY_COMMISSION: 'Вознаграждение компании',
    },

    // Information messages
    info: {
        LOADING: 'Рассчитываем стоимость...',
        COPIED: 'Результат скопирован в буфер обмена',
        SENT_TO_CHAT: 'Результат отправлен в чат',
        SW_REGISTERED: 'Service Worker зарегистрирован',
        SW_FAILED: 'Не удалось зарегистрировать Service Worker',
        META_LOADED: 'Метаданные загружены',
        META_FAILED: 'Не удалось загрузить метаданные',
        USING_FALLBACK: 'Используются резервные данные',
    },

    // Warning messages
    warnings: {
        NON_M1_DISCLAIMER: 'Расчет выполнен с допущениями для не-M1. Уточните условия у поддержки.',
        LARGE_MESSAGE: 'Сообщение слишком большое — отправляем краткую сводку',
        OPEN_VIA_BOT: 'Чтобы отправка работала, откройте калькулятор через кнопку в чате бота',
        WARNING_PREFIX: '⚠️ ',
    },

    // Placeholder texts
    placeholders: {
        SELECT_COUNTRY: 'Выберите страну',
    },

    // Age category labels
    age: {
        lt3: 'до 3 лет',
        '3_5': '3-5 лет',
        gt5: 'более 5 лет',
    },

    // Share/result text templates
    share: {
        TITLE: '🚗 Расчет растаможки',
        TITLE_FROM_COUNTRY: '🚗 Расчет растаможки из {country}: {total}',
        TITLE_GENERIC: '🚗 Расчет растаможки: {total}',
        BREAKDOWN_TITLE: 'Детализация:',
        WARNINGS_TITLE: 'Предупреждения:',
    },

    // Freight type labels (loaded from meta, but these are fallbacks)
    freight: {
        standard: 'Стандартный',
        open: 'Открытый',
        container: 'Контейнер',
    },

    // Vehicle type labels
    vehicle: {
        M1: 'Легковой (M1)',
        pickup: 'Пикап',
        bus: 'Автобус',
        motorhome: 'Дом на колесах',
        other: 'Другое',
    },

    // Country fallback labels (used if API meta fails)
    countries: {
        japan: '🍇 Япония',
        korea: '🍊 Корея',
        uae: '🍉 ОАЭ',
        china: '🍑 Китай',
        georgia: '🍒 Грузия',
    },

    // Currency labels
    currencies: {
        RUB: '₽',
        USD: '$',
        EUR: '€',
        JPY: '¥',
        CNY: '¥',
        AED: 'AED',
    },

    // Required field marker
    required: '*',

    // Duty formula display
    duty: {
        PERCENT_MODE: '{percent}% от стоимости (минимум по €/см³)',
        PER_CC_MODE: 'Ставка пошлины',
        VALUE_BRACKET: 'Диапазон до',
    },
};

// Export default for convenience
export default Messages;

