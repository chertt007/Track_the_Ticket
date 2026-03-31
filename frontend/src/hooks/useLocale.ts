import { useAppSelector } from './index'

/**
 * useLocale — returns a BCP 47 locale string based on Redux settings.language.
 * Use this to format dates and numbers in the correct locale.
 */
export function useLocale(): string {
  const language = useAppSelector(state => state.settings.language)
  return language === 'ru' ? 'ru-RU' : 'en-US'
}
