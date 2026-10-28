import { Menu, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CtaButton } from '@/components/landing/CtaButton'

const LINKS = [
  { href: '#how', label: 'How it works' },
  { href: '#agents', label: 'Agents' },
  { href: '#results', label: 'Results' },
  { href: '#privacy', label: 'Privacy' },
]

/** Bara de sus a paginii de prezentare: lipită sus, semi-transparentă; pe telefon, meniu care se deschide. */
export function LandingNav() {
  const [open, setOpen] = useState(false)
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  return (
    <header className="sticky top-0 z-40 border-b border-night-line bg-night-glass backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-8 px-4 sm:px-6 lg:px-8">
        <Link to="/about" className="flex items-center gap-2.5 rounded-sm focus-visible:outline-2 focus-visible:outline-brand" aria-label="ORB, home">
          <span className="grid h-8 w-8 place-items-center rounded-sm bg-brand font-condensed text-lg font-bold text-ink">O</span>
          <span className="text-lg font-bold tracking-tight">ORB</span>
        </Link>
        <nav aria-label="Page sections" className="hidden gap-7 md:flex">
          {LINKS.map((l) => (
            <a key={l.href} href={l.href} className="text-[15px] font-medium text-night-mute transition-colors hover:text-night-ink">{l.label}</a>
          ))}
        </nav>
        <div className="ml-auto hidden items-center gap-3 md:flex">
          <Link to="/dashboard" className="text-[15px] font-medium text-night-mute transition-colors hover:text-night-ink">Bank demo</Link>
          <CtaButton to="/arena" className="h-10 px-5">Try the Arena</CtaButton>
        </div>
        <button type="button" onClick={() => setOpen((o) => !o)} aria-expanded={open} aria-controls="landing-menu"
                className="ml-auto grid h-10 w-10 place-items-center rounded-sm text-night-ink md:hidden" aria-label={open ? 'Close menu' : 'Open menu'}>
          {open ? <X className="h-6 w-6" aria-hidden /> : <Menu className="h-6 w-6" aria-hidden />}
        </button>
      </div>
      {open && (
        <nav id="landing-menu" aria-label="Page sections" className="border-t border-night-line px-4 pb-6 pt-2 md:hidden">
          {LINKS.map((l) => (
            <a key={l.href} href={l.href} onClick={() => setOpen(false)} className="block border-b border-night-line py-4 text-lg font-medium">{l.label}</a>
          ))}
          <Link to="/dashboard" className="block py-4 text-lg font-medium text-night-mute">Bank demo</Link>
          <CtaButton to="/arena" className="mt-2 w-full">Try the Arena</CtaButton>
        </nav>
      )}
    </header>
  )
}
