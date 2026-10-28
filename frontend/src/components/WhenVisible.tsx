import { Suspense, useEffect, useRef, useState, type ReactNode } from 'react'

/**
 * Desenează conținutul abia când ajunge aproape de ecran. Pentru graficele grele (încărcate cu lazy):
 * pe telefon stau sub prima pagină, deci nu mai încetinesc prima afișare. Înălțimea din className
 * rezervă locul, ca pagina să nu sară când apare graficul.
 */
export function WhenVisible({ className, children }: { className: string; children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null)
  const [seen, setSeen] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el || seen) return
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) setSeen(true) }, { rootMargin: '200px' })
    io.observe(el)
    return () => io.disconnect()
  }, [seen])
  return <div ref={ref} className={className}>{seen && <Suspense fallback={null}>{children}</Suspense>}</div>
}
