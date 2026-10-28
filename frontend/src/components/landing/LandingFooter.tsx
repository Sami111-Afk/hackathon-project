import { Link } from 'react-router-dom'

const COLUMNS = [
  { title: 'Product', links: [{ href: '#how', label: 'How it works' }, { href: '#agents', label: 'Agents' }, { href: '#results', label: 'Results' }, { href: '#privacy', label: 'Privacy' }] },
  { title: 'Try it', links: [{ to: '/arena', label: 'Arena game' }, { to: '/cases/case_maria?mock=1', label: "Maria's application (demo)" }, { to: '/dashboard', label: 'Bank demo (sign in)' }] },
  { title: 'Arena', links: [{ to: '/arena/top', label: 'Leaderboard' }, { to: '/arena/live', label: 'Projector screen' }] },
]

/** Subsolul paginii de prezentare: logo, coloane de linkuri, nota despre datele fictive. */
export function LandingFooter() {
  return (
    <footer className="border-t border-night-line px-4 pb-10 pt-16 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-10 md:grid-cols-[minmax(0,2fr)_repeat(3,minmax(0,1fr))]">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="grid h-8 w-8 place-items-center rounded-sm bg-brand font-condensed text-lg font-bold text-ink">O</span>
            <span className="text-lg font-bold tracking-tight">ORB</span>
          </div>
          <p className="mt-4 max-w-xs leading-relaxed text-night-mute">AI agents that check loan documents. The analyst decides; personal data stays at the bank.</p>
        </div>
        {COLUMNS.map((c) => (
          <nav key={c.title} aria-label={c.title}>
            <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-night-mute">{c.title}</h2>
            <ul className="mt-4 space-y-3">
              {c.links.map((l) => (
                <li key={l.label}>
                  {'to' in l
                    ? <Link to={l.to} className="text-night-ink transition-colors hover:text-brand">{l.label}</Link>
                    : <a href={l.href} className="text-night-ink transition-colors hover:text-brand">{l.label}</a>}
                </li>
              ))}
            </ul>
          </nav>
        ))}
      </div>
      <p className="mx-auto mt-14 max-w-6xl border-t border-night-line pt-6 text-sm text-night-mute">
        Hackathon demo. All applicants shown are fictional; do not upload real documents.
      </p>
    </footer>
  )
}
