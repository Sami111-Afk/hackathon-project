import { useQuery } from '@tanstack/react-query'
import { EyeOff, FileDown, RotateCcw } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { AgentBand } from '@/components/AgentBand'
import { AppNav } from '@/components/AppNav'
import { DecisionPanel } from '@/components/DecisionPanel'
import { DocumentViewer } from '@/components/DocumentViewer'
import { FindingsList } from '@/components/FindingsList'
import { NetworkGraph } from '@/components/NetworkGraph'
import { PrivacyPanel } from '@/components/PrivacyPanel'
import { Panel } from '@/components/Panel'
import { VerdictCard } from '@/components/VerdictCard'
import { useCaseLive } from '@/hooks/useCaseLive'
import { getCase, getGraph, listCases, openReport, rerunDemo } from '@/lib/api'
import { isMock } from '@/lib/config'
import type { ConnectionState } from '@/lib/events'
import { AGENT_INFO } from '@/lib/labels'
import { AGENTS, type AgentName, type CaseStatus, type Finding } from '@/lib/types'
import { cn } from '@/lib/utils'

const CONN: Record<ConnectionState, { label: string; dot: string }> = {
  connecting: { label: 'Se conectează', dot: 'bg-ink-3' },
  live: { label: 'Actualizare live', dot: 'bg-ok' },
  reconnecting: { label: 'Se reconectează', dot: 'bg-warn' },
  replay: { label: 'Reluare demo', dot: 'bg-info' },
  closed: { label: 'Deconectat', dot: 'bg-ink-3' },
}

const STATUS: Record<CaseStatus, string> = {
  received: 'Primit', processing: 'În analiză', awaiting_review: 'Așteaptă decizia ta', cleared: 'Aprobat',
  rejected: 'Respins', escalated: 'La investigație', error: 'Eroare',
}

const lei = (n?: number | null) => (n ? `${n.toLocaleString('ro-RO')} lei` : '—')

/** `/cases/case_maria` (linkul din meniu) → cel mai recent dosar al Mariei; fiecare rulare a demo-ului are id nou. */
export function CasePage() {
  const { caseId = 'case_maria' } = useParams()
  const [latest, setLatest] = useState<string | null>(null)
  const alias = caseId === 'case_maria' && !isMock()
  useEffect(() => {
    if (!alias) return
    listCases()
      .then((cases) => {
        const maria = cases.filter((c) => c.id.startsWith('case_maria_'))
          .sort((a, b) => b.created_at.localeCompare(a.created_at))[0]
        setLatest(maria?.id ?? caseId)
      })
      .catch(() => setLatest(caseId))
  }, [alias, caseId])
  if (!alias) return <CaseView caseId={caseId} />
  if (latest === null) return <Shell><p className="p-8 text-lg text-ink-2">Se încarcă dosarul.</p></Shell>
  if (latest !== caseId) return <Navigate to={`/cases/${latest}`} replace />
  return <CaseView caseId={caseId} />
}

function CaseView({ caseId }: { caseId: string }) {
  const navigate = useNavigate()
  const [starting, setStarting] = useState(false)
  const runLive = () => {
    setStarting(true)
    rerunDemo()
      .then((id) => navigate(`/cases/${id}`))
      .catch(() => alert('Nu am putut porni analiza: serverul nu a răspuns.'))
      .finally(() => setStarting(false))
  }
  const [replayKey, setReplayKey] = useState(0)
  const { snapshot, state, dispatch, conn, mock } = useCaseLive(caseId, replayKey)
  const [selected, setSelected] = useState<Finding | null>(null)
  const [docId, setDocId] = useState('')

  const findings = useMemo(
    () => AGENTS.flatMap((a: AgentName) => (state.agents[a].result?.findings ?? []).map((finding) => ({ agent: a, finding }))),
    [state.agents],
  )
  const allFindings = findings.map((f) => f.finding)
  const lastDebate = [...state.feed].reverse().find((e) => e.type === 'debate')
  const fresh = useQuery({
    queryKey: ['case-fresh', caseId, state.agents.functionar.status, Boolean(state.verdict)],
    queryFn: () => getCase(caseId),
    enabled: !mock && (state.agents.functionar.status === 'done' || Boolean(state.verdict)),
    placeholderData: (prev) => prev,
  })

  // dosar deschis după ce Detectivul a terminat → graful nu a venit live, îl cerem o dată
  const detectivDone = state.agents.detectiv.status === 'done'
  const graphEmpty = state.graph.nodes.length === 0
  useEffect(() => {
    if (mock || !detectivDone || !graphEmpty) return
    getGraph(caseId).then((graph) => dispatch({ type: 'graph', graph })).catch(() => {})
  }, [mock, detectivDone, graphEmpty, caseId, dispatch])

  if (snapshot.isLoading) return <Shell><p className="p-8 text-lg text-ink-2">Se încarcă dosarul.</p></Shell>
  if (snapshot.isError || !snapshot.data) {
    return (
      <Shell>
        <div className="m-8 max-w-xl rounded-md border border-line bg-surface p-6">
          <h1 className="text-xl font-semibold text-ink">Dosarul nu s-a încărcat</h1>
          <p className="mt-2 text-ink-2">Serverul nu răspunde sau dosarul nu există. Verifică backend-ul, sau deschide demo-ul fără backend.</p>
          <Link to="/cases/case_maria?mock=1" className="mt-4 inline-block font-semibold text-info underline">Deschide demo-ul</Link>
        </div>
      </Shell>
    )
  }
  // dosarul citit la deschidere e cel de dinainte de agenți; după Funcționar și după verdict îl recitim
  const c = fresh.data ?? snapshot.data
  const status = state.decision ? ({ clear: 'cleared', reject: 'rejected', escalate: 'escalated', flag_network: 'escalated', correct: 'awaiting_review' } as const)[state.decision.action] : c.status
  const activeDoc = docId || c.documents[0]?.id || ''

  function select(f: Finding) {
    setSelected(f)
    if (f.evidence?.doc_id) setDocId(f.evidence.doc_id)
    document.getElementById('documente')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <Shell>
      <div className="border-b border-line bg-surface px-4 py-5 md:px-8">
        <nav className="text-sm text-ink-3"><Link to="/dashboard" className="hover:text-ink">Dosare</Link> / <span className="text-ink-2">{c.id}</span></nav>
        <div className="mt-2 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-ink">Cerere de credit de {lei(c.requested_amount_ron)}</h1>
            <p className="mt-1 text-base text-ink-2">
              {c.applicant_token ? `Solicitant ${c.applicant_token.startsWith('[') ? c.applicant_token : 'anonimizat'}, ` : ''}
              {c.documents.length} documente, depusă pe {new Date(c.created_at).toLocaleString('ro-RO', { dateStyle: 'long', timeStyle: 'short' })}
            </p>
            {c.applicant_token && (
              <p className="mt-1 flex items-center gap-1.5 text-sm text-ink-3">
                <EyeOff className="h-3.5 w-3.5" aria-hidden />
                Numele real e ascuns de Paznic: nici AI-ul, nici această pagină nu îl văd.
              </p>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-sm border border-line px-2.5 py-1 text-sm font-medium text-ink">{STATUS[status]}</span>
            <span className="flex items-center gap-2 text-sm text-ink-2"><span className={cn('h-2 w-2 rounded-full', CONN[conn].dot)} />{CONN[conn].label}</span>
            {mock ? (
              <button type="button" onClick={() => { setSelected(null); setReplayKey((k) => k + 1) }}
                className="flex h-10 items-center gap-2 rounded-sm border border-line bg-surface px-4 text-[15px] font-medium text-ink hover:bg-canvas">
                <RotateCcw className="h-4 w-4" aria-hidden /> Reia analiza
              </button>
            ) : (
              <>
              {caseId.startsWith('case_maria') && (
                <button type="button" disabled={starting || status === 'processing'} onClick={runLive}
                  className="flex h-10 items-center gap-2 rounded-sm border border-line bg-surface px-4 text-[15px] font-medium text-ink hover:bg-canvas disabled:opacity-40">
                  <RotateCcw className="h-4 w-4" aria-hidden /> {starting ? 'Pornește…' : 'Analizează din nou, live'}
                </button>
              )}
              <button type="button" disabled={!state.verdict} onClick={() => openReport(c.id).catch(() => alert('Raportul nu s-a generat: serverul nu a răspuns.'))}
                className="flex h-10 items-center gap-2 rounded-sm border border-line bg-surface px-4 text-[15px] font-medium text-ink hover:bg-canvas disabled:opacity-40">
                <FileDown className="h-4 w-4" aria-hidden /> Raport de anchetă
              </button>
              </>
            )}
          </div>
        </div>
      </div>

      <main className="space-y-6 px-4 py-6 md:px-8">
        <section aria-label="Agenții">
          <AgentBand agents={state.agents} />
          {lastDebate && (
            <p className="mt-3 border-l-2 border-ink pl-4 text-[15px] text-ink-2">
              <span className="font-semibold text-ink">{lastDebate.agent ? AGENT_INFO[lastDebate.agent].label : 'Biroul'}:</span> {lastDebate.message}
            </p>
          )}
        </section>

        {!mock && <PrivacyPanel caseId={c.id} ready={Boolean(state.verdict)} />}

        <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_440px]">
          <div className="space-y-6">
            <section id="documente" className="scroll-mt-4 rounded-md border border-line bg-surface">
              <DocumentViewer caseId={c.id} docs={c.documents} findings={allFindings} mock={mock}
                              highlighted={selected} docId={activeDoc} onDocChange={setDocId} />
            </section>
            <Panel title="Legături cu alte cereri" bodyClassName="p-0">
              <NetworkGraph graph={state.graph} height={320} />
            </Panel>
          </div>

          <aside className="space-y-6 xl:sticky xl:top-4">
            <section className="overflow-hidden rounded-md border border-line bg-surface">
              <VerdictCard verdict={state.verdict} />
              <DecisionPanel caseId={c.id} decision={state.decision} mock={mock} disabled={!state.verdict}
                             onDecided={(d) => dispatch({ type: 'decided', decision: d })} />
            </section>
            <Panel title="Dovezi" aside={<span className="text-sm text-ink-3">{findings.filter((f) => f.finding.severity !== 'info').length}</span>} bodyClassName="p-0">
              <FindingsList items={findings} onSelect={select} selected={selected} />
            </Panel>
          </aside>
        </div>
      </main>
    </Shell>
  )
}

function Shell({ children }: { children: React.ReactNode }) {
  return <div className="min-h-screen bg-canvas text-ink"><AppNav />{children}</div>
}
