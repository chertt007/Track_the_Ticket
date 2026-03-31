import { useAppSelector } from './index'
import { translations, TranslationKey } from '../i18n/translations'

/**
 * useT — translation hook, reads language from Redux settings.language
 * Usage: const t = useT(); t('addSubscription')
 */
export function useT() {
  const language = useAppSelector(state => state.settings.language)
  const dict = translations[language]
  return (key: TranslationKey): string => dict[key] ?? key
}
