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
    urlNotAviasales: 'Вставьте ссылку с Aviasales (aviasales.ru или aviasales.com)',

    // ScreenshotPreview
    screenshotAlt: 'Скриншот цены',
    clickToEnlarge: 'Нажмите для увеличения',
    close: 'Закрыть',

    // SubscriptionDetailPage
    backToDashboard: 'Назад',
    flightInfo: 'Информация о рейсе',
    priceHistory: 'История цен',
    screenshots: 'Скриншоты',
    noPriceData: 'Нет данных о ценах',
    noScreenshots: 'Нет скриншотов',
    subscriptionNotFound: 'Подписка не найдена',
    currentPrice: 'Текущая цена',
    minPrice: 'Минимум за 7 дней',
    maxPrice: 'Максимум за 7 дней',
    checkFrequencyLabel: 'Проверок в день',
    sourceLink: 'Ссылка на Aviasales',
    openLink: 'Открыть',
    statusFailed: 'Ошибка',
    statusOk: 'OK',

    // Settings
    settings: 'Настройки',
    language: 'Язык',
    russian: 'Русский',
    english: 'English',

    // PWA install prompt
    installTitle: 'Установить Track the Ticket',
    installHint: 'Добавьте на рабочий стол — работает как приложение',
    installAction: 'Установить',

    // Auth
    signInWithGoogle: 'Войти через Google',
    signingIn: 'Входим...',
    signOut: 'Выйти',
    authSubtitle: 'Автоматический мониторинг цен на авиабилеты',
    devBypass: 'Продолжить без авторизации (dev)',
    authError: 'Ошибка авторизации. Попробуйте ещё раз.',
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
    urlNotAviasales: 'Please paste an Aviasales link (aviasales.ru or aviasales.com)',

    // ScreenshotPreview
    screenshotAlt: 'Price screenshot',
    clickToEnlarge: 'Click to enlarge',
    close: 'Close',

    // SubscriptionDetailPage
    backToDashboard: 'Back',
    flightInfo: 'Flight Info',
    priceHistory: 'Price History',
    screenshots: 'Screenshots',
    noPriceData: 'No price data yet',
    noScreenshots: 'No screenshots yet',
    subscriptionNotFound: 'Subscription not found',
    currentPrice: 'Current price',
    minPrice: '7-day low',
    maxPrice: '7-day high',
    checkFrequencyLabel: 'Checks per day',
    sourceLink: 'Aviasales link',
    openLink: 'Open',
    statusFailed: 'Failed',
    statusOk: 'OK',

    // Settings
    settings: 'Settings',
    language: 'Language',
    russian: 'Русский',
    english: 'English',

    // PWA install prompt
    installTitle: 'Install Track the Ticket',
    installHint: 'Add to your desktop — works like a native app',
    installAction: 'Install',

    // Auth
    signInWithGoogle: 'Sign in with Google',
    signingIn: 'Signing in...',
    signOut: 'Sign out',
    authSubtitle: 'Automatic flight price monitoring',
    devBypass: 'Continue without auth (dev)',
    authError: 'Authentication error. Please try again.',
  },
}

export type TranslationKey = keyof typeof translations.ru
