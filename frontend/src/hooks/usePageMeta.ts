import { useEffect } from 'react'

/**
 * Titlul paginii și descrierea pentru Google / tab-ul browserului. Toate rutele împart același index.html,
 * deci le schimbăm din pagină; la ieșire revin cele de dinainte.
 */
export function usePageMeta(title: string, description?: string) {
  useEffect(() => {
    const meta = document.querySelector<HTMLMetaElement>('meta[name="description"]')
    const prev = { title: document.title, description: meta?.content }
    document.title = title
    if (meta && description) meta.content = description
    return () => {
      document.title = prev.title
      if (meta && prev.description !== undefined) meta.content = prev.description
    }
  }, [title, description])
}
