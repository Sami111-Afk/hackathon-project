import { useQuery } from '@tanstack/react-query'
import { EyeOff, FileDown, RotateCcw } from 'lucide-react'
import { lazy, useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { AgentBand } from '@/components/AgentBand'
import { AppNav } from '@/components/AppNav'
import { DecisionPanel } from '@/components/DecisionPanel'
import { DocumentViewer } from '@/components/DocumentViewer'
import { FindingsList } from '@/components/FindingsList'
import { PrivacyPanel } from '@/components/PrivacyPanel'
import { Panel } from '@/components/Panel'
import { VerdictCard } from '@/components/VerdictCard'
import { WhenVisible } from '@/components/WhenVisible'
import { useCaseLive } from '@/hooks/useCaseLive'
import { getCase, getGraph, listCases, openReport, rerunDemo } from '@/lib/api'
import { latestMariaId } from '@/lib/bankPages'
import { isMock } from '@/lib/config'
import type { ConnectionState } from '@/lib/events'
import { AGENT_INFO } from '@/lib/labels'
import { AGENTS, type AgentName, type CaseStatus, type Finding } from '@/lib/types'
import { cn } from '@/lib/utils'

// Graful (d3 + canvas) e sub documente: se încarcă doar când ajunge pe ecran.
const NetworkGraph = lazy(() => import('@/components/NetworkGraph').then((m) => ({ default: m.NetworkGraph })))

const CONN: Record<ConnectionState, { label: string; dot: string }> = {
  connecting: { label: 'Connecting', dot: 'bg-ink-3' },
  live: { label: 'Live updates', dot: 'bg-ok' },
  reconnecting: { label: 'Reconnecting', dot: 'bg-warn' },
  replay: { label: 'Demo replay', dot: 'bg-info' },
  closed: { label: 'Disconnected', dot: 'bg-ink-3' },
}

const STATUS: Record<CaseStatus, string> = {
  received: 'Received', processing: 'Under analysis', awaiting_review: 'Awaiting your decision', cleared: 'Approved',
  rejected: 'Rejected', escalated: 'Under investigation', error: 'Error',
}

const lei = (n?: number | null) => (n ? `${n.toLocaleString('en-GB')} lei` : '—')

/** `/cases/case_maria` (linkul din meniu) → cel mai recent dosar al Mariei; fiecare rulare a demo-ului are id nou. */
export function CasePage() {
  const { caseId = 'case_maria' } = useParams()
  const alias = caseId === 'case_maria' && !isMock()
  // Aceeași listă ca meniul și Dashboard-ul (cache comun), deci de obicei e deja aici.
  const cases = useQuery({ queryKey: ['cases', false], queryFn: listCases, enabled: alias })
  const latest = cases.data ? (latestMariaId(cases.data) ?? caseId) : cases.isError ? caseId : null
  if (!alias) return <CaseView caseId={caseId} />
  if (latest === null) return <Shell><p className="p-8 text-lg text-ink-2">Loading the application.</p></Shell>
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
      .catch(() => alert('Could not start the analysis: the server did not respond.'))
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

  // dosar deschis în timpul analizei: tipul documentelor și imaginea redactată apar abia după Paznic/Funcționar
  // → reîncărcăm dosarul când termină Funcționarul și la verdict (altfel taburile rămân „Necunoscut”, vederea AI 404)
  const functionarDone = state.agents.functionar.status === 'done'
  const hasVerdict = Boolean(state.verdict)
  const { refetch } = snapshot
  useEffect(() => {
    if (!mock && (functionarDone || hasVerdict)) refetch()
  }, [mock, functionarDone, hasVerdict, refetch])

  // dosar deschis după ce Detectivul a terminat → graful nu a venit live, îl cerem o dată
  const detectivDone = state.agents.detectiv.status === 'done'
  const graphEmpty = state.graph.nodes.length === 0
  useEffect(() => {
    if (mock || !detectivDone || !graphEmpty) return
    getGraph(caseId).then((graph) => dispatch({ type: 'graph', graph })).catch(() => {})
  }, [mock, detectivDone, graphEmpty, caseId, dispatch])

  if (snapshot.isLoading) return <Shell><p className="p-8 text-lg text-ink-2">Loading the application.</p></Shell>
  if (snapshot.isError || !snapshot.data) {
    return (
      <Shell>
        <div className="m-8 max-w-xl rounded-md border border-line bg-surface p-6">
          <h1 className="text-xl font-semibold text-ink">The application could not be loaded</h1>
          <p className="mt-2 text-ink-2">The server is not responding or the application does not exist. Check the backend, or open the demo without a backend.</p>
          <Link to="/cases/case_maria?mock=1" className="mt-4 inline-block font-semibold text-info underline">Open the demo</Link>
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
        <nav className="text-sm text-ink-3"><Link to="/dashboard" className="hover:text-ink">Applications</Link> / <span className="text-ink-2">{c.id}</span></nav>
        <div className="mt-2 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-ink">Loan application for {lei(c.requested_amount_ron)}</h1>
            <p className="mt-1 text-base text-ink-2">
              {c.applicant_token ? `Applicant ${c.applicant_token.startsWith('[') ? c.applicant_token : 'anonymized'}, ` : ''}
              {c.documents.length} documents, submitted on {new Date(c.created_at).toLocaleString('en-GB', { dateStyle: 'long', timeStyle: 'short' })}
            </p>
            {c.applicant_token && (
              <p className="mt-1 flex items-center gap-1.5 text-sm text-ink-3">
                <EyeOff className="h-3.5 w-3.5" aria-hidden />
                The real name is hidden by the Guard: neither the AI nor this page can see it.
              </p>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-sm border border-line px-2.5 py-1 text-sm font-medium text-ink">{STATUS[status]}</span>
            <span className="flex items-center gap-2 text-sm text-ink-2"><span className={cn('h-2 w-2 rounded-full', CONN[conn].dot)} />{CONN[conn].label}</span>
            {mock ? (
              <button type="button" onClick={() => { setSelected(null); setReplayKey((k) => k + 1) }}
                className="flex h-10 items-center gap-2 rounded-sm border border-line bg-surface px-4 text-[15px] font-medium text-ink hover:bg-canvas">
                <RotateCcw className="h-4 w-4" aria-hidden /> Replay analysis
              </button>
            ) : (
              <>
              {caseId.startsWith('case_maria') && (
                <button type="button" disabled={starting || status === 'processing'} onClick={runLive}
                  className="flex h-10 items-center gap-2 rounded-sm border border-line bg-surface px-4 text-[15px] font-medium text-ink hover:bg-canvas disabled:opacity-40">
                  <RotateCcw className="h-4 w-4" aria-hidden /> {starting ? 'Starting…' : 'Re-run live'}
                </button>
              )}
              <button type="button" disabled={!state.verdict} onClick={() => openReport(c.id).catch(() => alert('The report could not be generated: the server did not respond.'))}
                className="flex h-10 items-center gap-2 rounded-sm border border-line bg-surface px-4 text-[15px] font-medium text-ink hover:bg-canvas disabled:opacity-40">
                <FileDown className="h-4 w-4" aria-hidden /> Investigation report
              </button>
              </>
            )}
          </div>
        </div>
      </div>

      <main className="space-y-6 px-4 py-6 md:px-8">
        <section aria-label="Agents">
          <AgentBand agents={state.agents} />
          {lastDebate && (
            <p className="mt-3 border-l-2 border-ink pl-4 text-[15px] text-ink-2">
              <span className="font-semibold text-ink">{lastDebate.agent ? AGENT_INFO[lastDebate.agent].label : 'The office'}:</span> {lastDebate.message}
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
            <Panel title="Links to other applications" bodyClassName="p-0">
              <WhenVisible className="h-80"><NetworkGraph graph={state.graph} height={320} /></WhenVisible>
            </Panel>
          </div>

          <aside className="space-y-6 xl:sticky xl:top-4">
            <section className="overflow-hidden rounded-md border border-line bg-surface">
              <VerdictCard verdict={state.verdict} />
              <DecisionPanel caseId={c.id} decision={state.decision} mock={mock} disabled={!state.verdict}
                             recommendation={state.verdict?.recommendation}
                             onDecided={(d) => dispatch({ type: 'decided', decision: d })} />
            </section>
            <Panel title="Evidence" aside={<span className="text-sm text-ink-3">{findings.filter((f) => f.finding.severity !== 'info').length}</span>} bodyClassName="p-0">
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
