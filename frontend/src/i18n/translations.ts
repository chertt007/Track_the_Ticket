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
    airline: 'Авиакомпания',
    departure: 'Вылет',
    baggage: 'Багаж',
    active: 'Активна',
    inactive: 'Неактивна',
    lastChecked: 'Последняя проверка',
    never: 'Не проверялась',
    checkNow: 'Проверить сейчас',
    checking: 'Проверяем...',
    deleteSubscription: 'Удалить подписку',
    deleteConfirm: 'Удалить эту подписку? Это действие необратимо.',
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
    previewCheck: 'Проверить',
    previewLoading: 'Разбираем...',
    confirmTitle: 'Подтвердите рейс',
    confirmAirline: 'Авиакомпания',
    confirmPrice: 'Цена',
    confirmBaggageQuestion: 'Нужен ли багаж?',
    baggageYes: 'Да',
    baggageNo: 'Нет',
    confirmButton: 'Подтвердить',

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

    // Auth — Google
    signInWithGoogle: 'Войти через Google',
    signingIn: 'Входим...',
    signOut: 'Выйти',
    authSubtitle: 'Автоматический мониторинг цен на авиабилеты',
    devBypass: 'Продолжить без авторизации (dev)',
    authError: 'Ошибка авторизации. Попробуйте ещё раз.',

    // Auth — email/password form
    emailLabel: 'Email',
    passwordLabel: 'Пароль',
    confirmPasswordLabel: 'Подтвердите пароль',
    signInButton: 'Войти',
    orDivider: 'или',
    forgotPasswordLink: 'Забыли пароль?',
    registerLink: 'Зарегистрироваться',
    emailRequired: 'Введите email',
    passwordRequired: 'Введите пароль',
    passwordMismatch: 'Пароли не совпадают',
    codeRequired: 'Введите код',

    // Auth — sign up
    signUpTitle: 'Регистрация',
    registerButton: 'Создать аккаунт',
    alreadyHaveAccountLink: 'Уже есть аккаунт? Войти',

    // Auth — confirm email
    confirmSignUpTitle: 'Подтвердите email',
    confirmSignUpHint: 'Код отправлен на',
    codeLabel: 'Код из письма',
    confirmButton: 'Подтвердить',
    resendCodeLink: 'Отправить повторно',
    codeSentAgain: 'Код отправлен повторно.',
    confirmSuccessSignIn: 'Email подтверждён. Войдите.',

    // Auth — forgot password
    forgotPasswordTitle: 'Восстановление пароля',
    forgotPasswordHint: 'Введите email — отправим код для сброса пароля.',
    sendCodeButton: 'Отправить код',

    // Auth — new password
    newPasswordTitle: 'Новый пароль',
    newPasswordLabel: 'Новый пароль',
    savePasswordButton: 'Сохранить',
    passwordResetDone: 'Пароль изменён. Войдите с новым паролем.',

    // Auth — shared
    backLink: 'Назад',
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
    airline: 'Airline',
    departure: 'Departure',
    baggage: 'Baggage',
    active: 'Active',
    inactive: 'Inactive',
    lastChecked: 'Last checked',
    never: 'Never',
    checkNow: 'Check now',
    checking: 'Checking...',
    deleteSubscription: 'Delete subscription',
    deleteConfirm: 'Delete this subscription? This action cannot be undone.',
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
    previewCheck: 'Check',
    previewLoading: 'Parsing...',
    confirmTitle: 'Confirm flight',
    confirmAirline: 'Airline',
    confirmPrice: 'Price',
    confirmBaggageQuestion: 'Do you need baggage?',
    baggageYes: 'Yes',
    baggageNo: 'No',
    confirmButton: 'Confirm',

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

    // Auth — Google
    signInWithGoogle: 'Sign in with Google',
    signingIn: 'Signing in...',
    signOut: 'Sign out',
    authSubtitle: 'Automatic flight price monitoring',
    devBypass: 'Continue without auth (dev)',
    authError: 'Authentication error. Please try again.',

    // Auth — email/password form
    emailLabel: 'Email',
    passwordLabel: 'Password',
    confirmPasswordLabel: 'Confirm password',
    signInButton: 'Sign in',
    orDivider: 'or',
    forgotPasswordLink: 'Forgot password?',
    registerLink: 'Create account',
    emailRequired: 'Please enter your email',
    passwordRequired: 'Please enter your password',
    passwordMismatch: 'Passwords do not match',
    codeRequired: 'Please enter the code',

    // Auth — sign up
    signUpTitle: 'Create account',
    registerButton: 'Create account',
    alreadyHaveAccountLink: 'Already have an account? Sign in',

    // Auth — confirm email
    confirmSignUpTitle: 'Confirm your email',
    confirmSignUpHint: 'Code sent to',
    codeLabel: 'Verification code',
    confirmButton: 'Confirm',
    resendCodeLink: 'Resend code',
    codeSentAgain: 'Code resent.',
    confirmSuccessSignIn: 'Email confirmed. Please sign in.',

    // Auth — forgot password
    forgotPasswordTitle: 'Reset password',
    forgotPasswordHint: 'Enter your email and we\'ll send a reset code.',
    sendCodeButton: 'Send code',

    // Auth — new password
    newPasswordTitle: 'New password',
    newPasswordLabel: 'New password',
    savePasswordButton: 'Save',
    passwordResetDone: 'Password changed. Please sign in.',

    // Auth — shared
    backLink: 'Back',
  },
}

export type TranslationKey = keyof typeof translations.ru
