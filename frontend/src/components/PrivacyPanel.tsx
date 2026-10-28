import { Calculator, EyeOff, Lock, ShieldCheck } from 'lucide-react'
import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { apiFetch } from '@/lib/api'
import { cn } from '@/lib/utils'

// Dovezile de confidențialitate ale dosarului (GET /api/cases/{id}/privacy).
// Nimic nu e decriptat pentru afișare: arătăm ce stă pe disc, ce a primit AI-ul, calculul HE și rezultatul ZK.

interface Privacy {
  at_rest: {
    scheme: string
    documents: { doc_id: string; filename: string; encrypted_bytes: number; sample: string }[]
    vault: { labels: string[]; count: number; sample: string | null }
  }
  ai_saw: { llm_calls: number; with_pii: number; blocked: number; models: string[]; redacted_sample: string | null }
  homomorphic: null | {
    he_scheme: string; he_formula: string; he_ms: string; he_ciphertext_kb: string; he_context_kb: string
    he_ciphertext_sample: string; verifier_has_secret_key: boolean
  }
  zk: null | { answer: 'DA' | 'NU'; reason: string; threshold_ron?: number | null; employer?: string | null }
  prompt_injection_detected: boolean
}

const kb = (n: number) => `${Math.round(n / 1024).toLocaleString('ro-RO')} KB`

function Card({ icon, title, status, ok, children, proof }: {
  icon: ReactNode; title: string; status: string; ok: boolean | null; children: ReactNode; proof?: ReactNode
}) {
  return (
    <div className="flex flex-col rounded-md border border-line bg-surface p-4">
      <div className="flex items-center gap-2">
        <span className={cn('grid h-8 w-8 place-items-center rounded-sm',
          ok === null ? 'bg-canvas text-ink-3' : ok ? 'bg-ok-bg text-ok' : 'bg-danger-bg text-danger')}>{icon}</span>
        <div className="leading-tight">
          <div className="text-[15px] font-semibold text-ink">{title}</div>
          <div className={cn('text-sm font-medium', ok === null ? 'text-ink-3' : ok ? 'text-ok' : 'text-danger')}>{status}</div>
        </div>
      </div>
      <div className="mt-3 text-sm text-ink-2">{children}</div>
      {proof && (
        <details className="mt-3 text-sm">
          <summary className="cursor-pointer font-medium text-ink hover:underline">Vezi dovada</summary>
          <div className="mt-2 space-y-2">{proof}</div>
        </details>
      )}
    </div>
  )
}

const Mono = ({ children }: { children: ReactNode }) => (
  <pre className="max-h-48 overflow-auto whitespace-pre-wrap break-all rounded-sm bg-canvas p-2 font-mono text-xs text-ink-2">{children}</pre>
)

export function PrivacyPanel({ caseId, ready }: { caseId: string; ready: boolean }) {
  const [data, setData] = useState<Privacy | null>(null)
  const [error, setError] = useState(false)
  const [zkBusy, setZkBusy] = useState(false)

  const load = useCallback(() => {
    apiFetch(`/api/cases/${encodeURIComponent(caseId)}/privacy`)
      .then((r) => r.json())
      .then((d: Privacy) => { setData(d); setError(false) })
      .catch(() => setError(true))
  }, [caseId])

  useEffect(() => { if (ready) load() }, [ready, load])

  const askZk = () => {
    setZkBusy(true)
    apiFetch('/api/zk/demo', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ case_id: caseId }),
    })
      .then(load)
      .catch(() => alert('Dovada ZK nu a putut fi generată: serverul nu a răspuns.'))
      .finally(() => setZkBusy(false))
  }

  if (!ready) return null
  if (error) return <p className="text-sm text-ink-3">Dovezile de confidențialitate nu s-au încărcat.</p>
  if (!data) return <p className="text-sm text-ink-3">Se încarcă dovezile de confidențialitate.</p>

  const { at_rest: rest, ai_saw: ai, homomorphic: he, zk } = data
  const totalEnc = rest.documents.reduce((s, d) => s + d.encrypted_bytes, 0)

  return (
    <section aria-label="Confidențialitate" className="space-y-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-semibold text-ink">Confidențialitate — ce poate demonstra banca</h2>
        <span className="text-sm text-ink-3">Nimic nu e decriptat pentru această pagină.</span>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card icon={<Lock className="h-4 w-4" />} title="Criptat pe disc" ok={rest.documents.length > 0}
          status={`${rest.documents.length} documente · ${rest.vault.count} valori în seif`}
          proof={<>
            {rest.documents.map((d) => (
              <div key={d.doc_id}><div className="text-xs text-ink-3">{d.filename} · {kb(d.encrypted_bytes)} pe disc</div><Mono>{d.sample}</Mono></div>
            ))}
            {rest.vault.sample && <div><div className="text-xs text-ink-3">Seif: {rest.vault.labels.join(' ')}</div><Mono>{rest.vault.sample}</Mono></div>}
          </>}>
          Fișierele ({kb(totalEnc)}) și datele personale stau criptate ({rest.scheme.split(' ')[0]}, AES). Pe disc nu există o imagine sau un CNP în clar.
        </Card>

        <Card icon={<EyeOff className="h-4 w-4" />} title="AI-ul n-a văzut date personale" ok={ai.with_pii === 0}
          status={`${ai.llm_calls} apeluri AI · ${ai.with_pii} cu date personale`}
          proof={ai.redacted_sample ? <><div className="text-xs text-ink-3">Textul exact primit de AI:</div><Mono>{ai.redacted_sample}</Mono></> : undefined}>
          AI-ul lucrează pe etichete ca [PERSOANA_1] și [CNP_1]. Chiar păcălit printr-un text ascuns, nu are ce date reale să scape.
          {ai.blocked > 0 && ` Poarta anti-date-personale a blocat ${ai.blocked} cereri.`}
          {data.prompt_injection_detected && <span className="mt-1 block font-medium text-danger">Documentul conține un text care încearcă să păcălească AI-ul.</span>}
        </Card>

        <Card icon={<Calculator className="h-4 w-4" />} title="Calcul pe date criptate" ok={he ? true : null}
          status={he ? `${he.he_scheme.split(',')[0]} · ${he.he_ms} ms` : 'nefolosit la acest dosar'}
          proof={he ? <>
            <div className="text-xs text-ink-3">Formula calculată pe ciphertext: {he.he_formula}</div>
            <div className="text-xs text-ink-3">Primii octeți din salariul criptat ({he.he_ciphertext_kb} KB):</div>
            <Mono>{he.he_ciphertext_sample}…</Mono>
          </> : undefined}>
          {he
            ? <>Taxele de pe fluturaș au fost refăcute de un verificator care a primit doar sumele criptate și <b>nu are cheia</b>. Banca decriptează doar rezultatul.</>
            : 'Fluturașul nu a avut sume citibile pentru verificarea criptată.'}
        </Card>

        <Card icon={<ShieldCheck className="h-4 w-4" />} title="Venit dovedit fără să-l vedem" ok={zk ? zk.answer === 'DA' : null}
          status={zk ? `Răspuns ZK: ${zk.answer}` : 'încă necerut'}>
          {zk
            ? <>{zk.reason}{zk.threshold_ron ? ` (prag ${zk.threshold_ron.toLocaleString('ro-RO')} lei` : ''}{zk.employer ? `, atestat de ${zk.employer})` : zk.threshold_ron ? ')' : ''}.</>
            : 'Clientul poate dovedi că venitul lui trece pragul cerut, fără să-l arate băncii (zero-knowledge).'}
          <button type="button" onClick={askZk} disabled={zkBusy}
            className="mt-3 flex h-9 items-center rounded-sm border border-line px-3 text-sm font-medium text-ink hover:bg-canvas disabled:opacity-40">
            {zkBusy ? 'Se generează dovada…' : zk ? 'Cere din nou' : 'Cere dovadă de venit'}
          </button>
        </Card>
      </div>
    </section>
  )
}
