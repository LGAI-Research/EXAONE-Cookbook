import { computed } from 'vue'
import { useData, withBase } from 'vitepress'
import type { L10n, L10nList, Lang } from '../data/site'

/**
 * Locale helpers shared by every custom component. Content lives in the data
 * modules with `en` / `ko` fields, so components never duplicate copy.
 */
export function useLocale() {
  const { lang } = useData()

  const locale = computed<Lang>(() => (lang.value.startsWith('ko') ? 'ko' : 'en'))

  const t = (value: L10n) => value[locale.value]
  const tl = (value: L10nList) => value[locale.value]

  /** Prefix an internal path with the locale segment and the site base. */
  const link = (path: string) =>
    withBase(locale.value === 'ko' ? `/ko${path}` : path)

  return { locale, t, tl, link }
}
