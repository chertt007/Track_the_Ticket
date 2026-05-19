# Mobile Sign-In Fix

---

## Симптом

На мобильных устройствах: нажимаешь Sign in with Google → открывается Google OAuth
окно/редирект → нажимаешь Continue → возвращаешься на страницу sign-in вместо dashboard.
На десктопе всё работает.

---

## Root Cause

### Что происходит

Код в `LoginPage.tsx` разделяет логику по ширине экрана:
- **Desktop (>768px):** `signInWithPopup()` — работает
- **Mobile (≤768px):** `signInWithRedirect()` — не работает

`signInWithRedirect` делает следующее:
1. Перенаправляет пользователя на Google OAuth
2. Google редиректит обратно на Firebase Auth handler: `https://PROJECT.firebaseapp.com/__/auth/handler`
3. Firebase обрабатывает результат и редиректит обратно на `https://track-the-ticket.com`
4. Приложение загружается, Firebase SDK пытается прочитать результат редиректа

### Где ломается

`authDomain` в Firebase конфиге (`VITE_FIREBASE_AUTH_DOMAIN`) = `project.firebaseapp.com`.
Приложение живёт на `track-the-ticket.com`.

Это **разные домены**. Когда приложение загружается после редиректа, Firebase SDK
пытается прочитать сохранённое состояние OAuth через cross-origin storage
(cookies / IndexedDB). Современные мобильные браузеры (Safari iOS 13.4+, Chrome на Android)
**блокируют cross-origin cookies и storage** по умолчанию.

Результат: `onAuthStateChanged` срабатывает с `null`, пользователь остаётся на `/login`.

### Дополнительный фактор

В `useAuth.ts` не вызывается `getRedirectResult(auth)` — это тоже нужно для явной
обработки результата редиректа, хотя и не является главной причиной.

---

## Решения

### Вариант A — Использовать `signInWithPopup` везде (рекомендуется, быстрый фикс)

Убрать условие `isMobile()` и использовать `signInWithPopup` на всех платформах.

**Почему работает:** `signInWithPopup` не требует cross-origin storage — результат
передаётся напрямую в открытом окне в том же браузерном контексте. На мобильных
браузерах popup открывается, если вызван непосредственно из обработчика тапа (что и есть).

**Изменения:** 3 строки в `LoginPage.tsx` — убрать `isMobile()`, оставить только `signInWithPopup`.

**Минус:** Popup на мобиле выглядит немного хуже UX (маленькое окошко), но функционально работает.

---

### Вариант B — Сменить `authDomain` на кастомный домен (правильное решение, сложнее)

Выставить `authDomain: "track-the-ticket.com"` в Firebase конфиге.
Тогда auth handler живёт на том же домене — cross-origin проблемы нет.

**Требует:**
1. Настроить Firebase Hosting для проксирования `/__/firebase/` и `/__/auth/` путей
2. Добавить `VITE_FIREBASE_AUTH_DOMAIN=track-the-ticket.com` в GitHub Secrets
3. Настроить authorized redirect URIs в Google Cloud Console OAuth client

**Плюс:** Сохраняет redirect-flow, более правильная архитектура.
**Минус:** Значительно сложнее в настройке, требует Firebase Hosting или Caddy proxy rules.

---

## План реализации (Вариант A)

**Приоритет: сначала A, потом при необходимости B.**

### Шаг 1 — Убрать `isMobile()` из `LoginPage.tsx`

```tsx
// Было:
if (isMobile()) {
  await signInWithRedirect(auth, googleProvider)
} else {
  await signInWithPopup(auth, googleProvider)
}

// Станет:
await signInWithPopup(auth, googleProvider)
```

Также удалить `isMobile()` функцию и импорт `signInWithRedirect`.

### Шаг 2 — Добавить `getRedirectResult` в `useAuth.ts` (на всякий случай)

Для пользователей, которые могли начать redirect до фикса — обработать pending результат:

```ts
import { onAuthStateChanged, getRedirectResult } from 'firebase/auth'

useEffect(() => {
  getRedirectResult(auth).catch(() => {}) // clear any pending redirect state
  return onAuthStateChanged(auth, ...)
}, [dispatch])
```

### Шаг 3 — Задеплоить

```powershell
git add frontend/src/pages/LoginPage.tsx frontend/src/hooks/useAuth.ts
git commit -m "fix: use signInWithPopup on all platforms, fixes mobile auth"
git push
```

---

## Задачи

- ✅ Задокументировать root cause и план
- 🔄 Убрать `isMobile()` из `LoginPage.tsx`, оставить только `signInWithPopup`
- 🔄 Добавить `getRedirectResult` cleanup в `useAuth.ts`
- ⬜ Задеплоить и проверить на мобиле

---

## История попыток

### Попытка 1 — Вариант A (2026-05-19)
Убираем `signInWithRedirect` полностью, используем `signInWithPopup` на всех платформах.
Если не поможет — переходим к Варианту B (кастомный authDomain).
