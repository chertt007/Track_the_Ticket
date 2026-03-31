export const translations = {
  ru: {
    // AppBar
    appName: 'Track the Ticket',
    dashboard: 'Дашборд',
    login: 'Войти',

    // Dashboard
    mySubscriptions: 'Мои подписки',
    addSubscription: 'Добавить подписку',
    subscriptionOne: 'подписка',
    subscriptionFew: 'подписки',
    subscriptionMany: 'подписок',
    noSubscriptions: 'Нет активных подписок',
    noSubscriptionsHint: 'Добавьте ссылку с Aviasales, чтобы начать отслеживать цены',

    // SubscriptionCard
    flight: 'Рейс',
    departure: 'Вылет',
    baggage: 'Багаж',
    active: 'Активна',
    inactive: 'Неактивна',
    lastChecked: 'Последняя проверка',
    never: 'Не проверялась',
    checkNow: 'Проверить сейчас',
    checking: 'Проверяем...',
    lastPrice: 'Последняя цена',

    // AddSubscriptionModal
    addSubscriptionTitle: 'Добавить подписку',
    urlLabel: 'Ссылка с Aviasales',
    urlPlaceholder: 'https://www.aviasales.ru/search/...',
    urlHint: 'Скопируйте ссылку с результатами поиска на Aviasales',
    cancel: 'Отмена',
    add: 'Добавить',
    urlRequired: 'Введите ссылку',
    urlInvalid: 'Введите корректную ссылку (начинается с http)',

    // ScreenshotPreview
    screenshotAlt: 'Скриншот цены',
    clickToEnlarge: 'Нажмите для увеличения',
    close: 'Закрыть',

    // Settings
    settings: 'Настройки',
    language: 'Язык',
    russian: 'Русский',
    english: 'English',
  },

  en: {
    // AppBar
    appName: 'Track the Ticket',
    dashboard: 'Dashboard',
    login: 'Login',

    // Dashboard
    mySubscriptions: 'My Subscriptions',
    addSubscription: 'Add Subscription',
    subscriptionOne: 'subscription',
    subscriptionFew: 'subscriptions',
    subscriptionMany: 'subscriptions',
    noSubscriptions: 'No active subscriptions',
    noSubscriptionsHint: 'Add an Aviasales link to start tracking prices',

    // SubscriptionCard
    flight: 'Flight',
    departure: 'Departure',
    baggage: 'Baggage',
    active: 'Active',
    inactive: 'Inactive',
    lastChecked: 'Last checked',
    never: 'Never',
    checkNow: 'Check now',
    checking: 'Checking...',
    lastPrice: 'Last price',

    // AddSubscriptionModal
    addSubscriptionTitle: 'Add Subscription',
    urlLabel: 'Aviasales link',
    urlPlaceholder: 'https://www.aviasales.ru/search/...',
    urlHint: 'Copy the search results link from Aviasales',
    cancel: 'Cancel',
    add: 'Add',
    urlRequired: 'Please enter a URL',
    urlInvalid: 'Please enter a valid URL (must start with http)',

    // ScreenshotPreview
    screenshotAlt: 'Price screenshot',
    clickToEnlarge: 'Click to enlarge',
    close: 'Close',

    // Settings
    settings: 'Settings',
    language: 'Language',
    russian: 'Русский',
    english: 'English',
  },
}

export type TranslationKey = keyof typeof translations.ru
