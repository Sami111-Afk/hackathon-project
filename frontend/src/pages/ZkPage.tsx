import { useMutation } from '@tanstack/react-query'
import { Building2, CheckCircle2, EyeOff, Landmark, ShieldAlert, Smartphone, XCircle } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { AppNav } from '@/components/AppNav'
import { Panel } from '@/components/Panel'
import { isMock } from '@/lib/config'
import { cn } from '@/lib/utils'
import { ATTACKS, DSTI, EMPLOYERS, mockZkDemo, runZkDemo, type ZkAttack, type ZkDemoRequest, type ZkDemoResult } from '@/lib/zk'

const BTN = 'h-11 rounded-sm px-4 text-[15px] font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-info'
const FIELD = 'h-11 w-full rounded-sm border border-input bg-surface px-3 text-base outline-none focus:border-info'

const ACTOR_ICON: Record<string, typeof Landmark> = {
  bancă: Landmark, angajator: Building2, client: Smartphone, atacator: ShieldAlert,
}

const ron = (n: number) => `${n.toLocaleString('ro-RO', { minimumFractionDigits: 0, maximumFractionDigits: 2 })} lei`

function lastMonth(): string {
  const d = new Date()
  d.setDate(1)
  d.setMonth(d.getMonth() - 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function Answer({ r }: { r: ZkDemoResult }) {
  const Icon = r.ok ? CheckCircle2 : XCircle
  return (
    <div className={cn('flex items-start gap-5 rounded-md border px-6 py-5', r.ok ? 'border-ok bg-ok-bg' : 'border-danger bg-danger-bg')}>
      <Icon className={cn('mt-1 h-12 w-12 shrink-0', r.ok ? 'text-ok' : 'text-danger')} aria-hidden />
      <div>
        <div className={cn('font-condensed text-6xl font-bold leading-none', r.ok ? 'text-ok' : 'text-danger')}>{r.answer}</div>
        <p className="mt-2 text-xl text-ink">{r.reason}</p>
        {r.threshold_ron != null && (
          <p className="mt-1 text-base text-ink-2">
            Întrebarea băncii: venitul net e cel puțin {ron(r.threshold_ron)}?
            {r.employer ? ` Angajator: ${r.employer}.` : ''}
          </p>
        )}
      </div>
    </div>
  )
}

function Timeline({ steps }: { steps: ZkDemoResult['steps'] }) {
  return (
    <ol className="space-y-0">
      {steps.map((s, i) => {
        const Icon = ACTOR_ICON[s.actor] ?? Landmark
        const bad = s.actor === 'atacator' || s.action.startsWith('nu ')
        return (
          <li key={i} className="flex gap-4">
            <div className="flex flex-col items-center">
              <span className={cn('grid h-10 w-10 place-items-center rounded-full border',
                bad ? 'border-danger bg-danger-bg text-danger' : 'border-line bg-canvas text-ink')}>
                <Icon className="h-5 w-5" aria-hidden />
              </span>
              {i < steps.length - 1 && <span className="w-px flex-1 bg-line" />}
            </div>
            <div className="pb-5 pt-1.5">
              <div className="text-lg font-semibold text-ink">
                <span className="capitalize">{s.actor}</span> <span className="font-normal text-ink-2">· {s.action}</span>
              </div>
              <div className="text-base text-ink-2">{s.detail}</div>
            </div>
          </li>
        )
      })}
    </ol>
  )
}

function BankSaw({ r }: { r: ZkDemoResult }) {
  const s = r.bank_saw
  if (!s) return <p className="text-base text-ink-3">Banca nu a primit nicio dovadă: clientul n-a putut-o genera.</p>
  const rows: [string, string][] = [
    ['Angajator (CUI)', s.cui],
    ['Perioada', s.period],
    ['Angajament', `${s.commitment.slice(0, 14)}…${s.commitment.slice(-6)}`],
    ['Dovada', `${s.proof_bytes.toLocaleString('ro-RO')} octeți`],
  ]
  return (
    <div className="space-y-4">
      <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-base">
        {rows.map(([k, v]) => (
          <div key={k} className="contents">
            <dt className="text-ink-2">{k}</dt>
            <dd className="font-mono text-ink">{v}</dd>
          </div>
        ))}
      </dl>
      <p className="flex items-center gap-2 rounded-sm border border-ok bg-ok-bg px-4 py-3 text-base font-semibold text-ok">
        <EyeOff className="h-5 w-5" aria-hidden /> Salariul nu apare nicăieri în ce a primit banca.
      </p>
    </div>
  )
}

export function ZkPage() {
  const mock = isMock()
  const [salary, setSalary] = useState('8307')
  const [installment, setInstallment] = useState('2500')
  const [cui, setCui] = useState(EMPLOYERS[0].cui)
  const [period, setPeriod] = useState(lastMonth)
  const [attack, setAttack] = useState<ZkAttack>('none')

  const run = useMutation({
    mutationFn: async (body: ZkDemoRequest) => (mock ? mockZkDemo(body) : runZkDemo(body)),
  })

  const salaryN = Number(salary.replace(',', '.'))
  const installmentN = Number(installment.replace(',', '.'))
  const valid = salaryN >= 0 && installmentN > 0 && /^\d{4}-(0[1-9]|1[0-2])$/.test(period)

  function submit(e: FormEvent) {
    e.preventDefault()
    if (valid) run.mutate({ net_salary_ron: salaryN, installment_ron: installmentN, cui, period, attack })
  }

  const r = run.data

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <AppNav />
      <div className="border-b border-line bg-surface px-4 py-5 md:px-8">
        <h1 className="text-3xl font-semibold tracking-tight">Dovadă de venit fără salariu</h1>
        <p className="mt-1 text-base text-ink-2">
          Clientul dovedește că venitul net atestat de angajator acoperă rata, fără ca banca să afle salariul (zero-knowledge).
        </p>
        {mock && (
          <p className="mt-4 rounded-sm border border-warn bg-warn-bg px-4 py-3 text-base font-semibold text-warn">
            Date de demo: răspunsurile sunt simulate în browser, fără dovezi reale de la backend.
          </p>
        )}
      </div>

      <main className="grid gap-6 px-4 py-6 md:px-8 xl:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <Panel title="Cererea">
          <form onSubmit={submit} className="space-y-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block space-y-1.5">
                <span className="text-sm font-medium text-ink-2">Salariu net (lei, îl știe doar clientul)</span>
                <input className={FIELD} inputMode="decimal" value={salary} onChange={(e) => setSalary(e.target.value)} />
              </label>
              <label className="block space-y-1.5">
                <span className="text-sm font-medium text-ink-2">Rata lunară (lei)</span>
                <input className={FIELD} inputMode="decimal" value={installment} onChange={(e) => setInstallment(e.target.value)} />
              </label>
              <label className="block space-y-1.5">
                <span className="text-sm font-medium text-ink-2">Angajator</span>
                <select className={FIELD} value={cui} onChange={(e) => setCui(e.target.value)}>
                  {EMPLOYERS.map((e) => <option key={e.cui} value={e.cui}>{e.name}</option>)}
                </select>
              </label>
              <label className="block space-y-1.5">
                <span className="text-sm font-medium text-ink-2">Luna atestată</span>
                <input className={FIELD} type="month" value={period} onChange={(e) => setPeriod(e.target.value)} />
              </label>
            </div>
            {installmentN > 0 && (
              <p className="text-base text-ink-2">
                Prag cerut de bancă: rata / {DSTI.toLocaleString('ro-RO')} = <span className="font-semibold text-ink">{ron(Math.round(installmentN / DSTI * 100) / 100)}</span>
              </p>
            )}

            <fieldset className="space-y-2">
              <legend className="mb-2 text-sm font-medium text-ink-2">Încercare de fraudă</legend>
              {ATTACKS.map((a) => (
                <label key={a.id} className={cn('flex cursor-pointer items-start gap-3 rounded-sm border px-4 py-3',
                  attack === a.id ? 'border-ink bg-canvas' : 'border-line hover:bg-canvas/60')}>
                  <input type="radio" name="attack" value={a.id} checked={attack === a.id} onChange={() => setAttack(a.id)}
                         className="mt-1 h-4 w-4 accent-ink" />
                  <span>
                    <span className="block text-base font-semibold text-ink">{a.label}</span>
                    <span className="block text-sm text-ink-2">{a.hint}</span>
                  </span>
                </label>
              ))}
            </fieldset>

            <button type="submit" disabled={!valid || run.isPending} className={cn(BTN, 'w-full bg-ink text-white hover:bg-black')}>
              {run.isPending ? 'Se generează și se verifică dovada…' : 'Cere dovada'}
            </button>
            {run.isError && <p className="text-base text-danger">{run.error.message}</p>}
          </form>
        </Panel>

        <div className="space-y-6">
          {r ? (
            <>
              <Answer r={r} />
              <Panel title="Ce s-a întâmplat"><Timeline steps={r.steps} /></Panel>
              <Panel title="Ce a văzut banca"><BankSaw r={r} /></Panel>
            </>
          ) : (
            <Panel title="Rezultatul">
              <p className="text-lg text-ink-2">
                Completează cererea și apasă „Cere dovada”. Banca primește doar angajamentul semnat de angajator și dovada,
                apoi răspunde DA sau NU. Alege o încercare de fraudă ca să vezi că fiecare e respinsă.
              </p>
            </Panel>
          )}
        </div>
      </main>
    </div>
  )
}
