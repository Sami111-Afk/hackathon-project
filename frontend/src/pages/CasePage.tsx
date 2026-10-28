import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { AgentBand } from '@/components/AgentBand'
import { DecisionPanel } from '@/components/DecisionPanel'
import { DocumentViewer } from '@/components/DocumentViewer'
import { FindingsList } from '@/components/FindingsList'
import { NetworkGraph } from '@/components/NetworkGraph'
import { VerdictCard } from '@/components/VerdictCard'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useCaseLive } from '@/hooks/useCaseLive'
import { getGraph } from '@/lib/api'
import { logout } from '@/lib/auth'
import { AGENT_INFO } from '@/lib/labels'
import { AGENTS, type AgentName, type Finding } from '@/lib/types'
import type { ConnectionState } from '@/lib/events'

const CONN: Record<ConnectionState, string> = {
  connecting: '⏳ conectare…',
  live: '🟢 live',
  reconnecting: '🟠 reconectare…',
  replay: '▶️ replay (mock)',
  closed: '⚪ deconectat',
}

export function CasePage() {
  const { caseId = 'case_maria' } = useParams()
  const [replayKey, setReplayKey] = useState(0)
  const { snapshot, state, dispatch, conn, mock } = useCaseLive(caseId, replayKey)
  const [selected, setSelected] = useState<Finding | null>(null)

  const findings = useMemo(
    () => AGENTS.flatMap((a: AgentName) => (state.agents[a].result?.findings ?? []).map((finding) => ({ agent: a, finding }))),
    [state.agents],
  )
  const allFindings = findings.map((f) => f.finding)
  const lastDebate = [...state.feed].reverse().find((e) => e.type === 'debate')

  // Dosar deschis după ce Detectivul a terminat → n-am prins graful live, îl cerem o dată.
  const detectivDone = state.agents.detectiv.status === 'done'
  const graphEmpty = state.graph.nodes.length === 0
  useEffect(() => {
    if (mock || !detectivDone || !graphEmpty) return
    getGraph(caseId).then((graph) => dispatch({ type: 'graph', graph })).catch(() => {})
  }, [mock, detectivDone, graphEmpty, caseId, dispatch])

  if (snapshot.isLoading) return <div className="p-8 text-xl">Se încarcă dosarul…</div>
  if (snapshot.isError || !snapshot.data) {
    return <div className="p-8 text-xl text-red-700">Dosarul nu a putut fi încărcat. Verifică backend-ul sau deschide cu <code>?mock=1</code>.</div>
  }
  const c = snapshot.data
  // dacă un finding e selectat, arătăm documentul lui primul
  const docs = selected?.evidence?.doc_id
    ? [...c.documents].sort((a, b) => (a.id === selected.evidence!.doc_id ? -1 : b.id === selected.evidence!.doc_id ? 1 : 0))
    : c.documents

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b bg-white px-4 py-3 md:px-6">
        <div>
          <h1 className="text-2xl font-bold">🔒 ORB · Dosar {c.id}</h1>
          <p className="text-slate-600">
            Solicitant {c.applicant_token} · credit {c.requested_amount_ron?.toLocaleString('ro-RO')} lei · {c.documents.length} documente
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-base">{CONN[conn]}</span>
          {mock && <Button variant="outline" onClick={() => { setSelected(null); setReplayKey((k) => k + 1) }}>↻ Reia demo</Button>}
          {!mock && <Button variant="ghost" onClick={() => { logout(); window.location.assign('/login') }}>Ieșire</Button>}
        </div>
      </header>

      <main className="space-y-6 p-4 md:p-6">
        <section>
          <AgentBand agents={state.agents} />
          {lastDebate && (
            <p className="mt-3 rounded-lg border border-blue-200 bg-blue-50 p-3 text-base">
              💬 <b>{lastDebate.agent ? AGENT_INFO[lastDebate.agent].label : 'Birou'}:</b> {lastDebate.message}
            </p>
          )}
        </section>

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_420px]">
          <section className="space-y-8">
            <Card>
              <CardHeader><CardTitle className="text-xl">🕵️ Rețeaua Detectivului</CardTitle></CardHeader>
              <CardContent><NetworkGraph graph={state.graph} /></CardContent>
            </Card>
            {docs.map((d) => (
              <Card key={d.id}>
                <CardContent className="pt-6">
                  <DocumentViewer caseId={c.id} doc={d} findings={allFindings} mock={mock} highlighted={selected} />
                </CardContent>
              </Card>
            ))}
          </section>

          <aside className="space-y-6 lg:sticky lg:top-4 lg:self-start">
            <VerdictCard verdict={state.verdict} />
            <DecisionPanel
              caseId={c.id}
              decision={state.decision}
              mock={mock}
              disabled={!state.verdict}
              onDecided={(d) => dispatch({ type: 'decided', decision: d })}
            />
            <Card>
              <CardHeader><CardTitle className="text-xl">Ce au găsit agenții</CardTitle></CardHeader>
              <CardContent><FindingsList items={findings} onSelect={setSelected} selected={selected} /></CardContent>
            </Card>
          </aside>
        </div>
      </main>
    </div>
  )
}
