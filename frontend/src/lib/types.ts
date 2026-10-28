// Oglinda lui backend/app/models.py. Contractul se schimbă acolo, nu aici.

export type AgentName = 'paznic' | 'functionar' | 'verificator' | 'detector' | 'detectiv' | 'compliance'
export type Severity = 'info' | 'low' | 'medium' | 'high' | 'critical'
export type AgentStatus = 'pending' | 'running' | 'done' | 'error' | 'skipped'
export type CaseStatus =
  | 'received' | 'processing' | 'awaiting_review' | 'cleared' | 'rejected' | 'escalated' | 'error'
export type DocType =
  | 'id_card' | 'payslip' | 'bank_statement' | 'employment_certificate' | 'other' | 'unknown'
export type EventType =
  | 'case_created' | 'agent_started' | 'agent_progress' | 'agent_finished' | 'agent_error'
  | 'debate' | 'verdict' | 'decision' | 'rule_proposed' | 'rule_approved' | 'arena_scored' | 'ping'

export interface Evidence {
  doc_id?: string | null
  page?: number | null
  bbox?: [number, number, number, number] | null // [x0, y0, x1, y1] px, origine stânga-sus
  field?: string | null
}

export interface Finding {
  code: string
  severity: Severity
  message: string
  evidence?: Evidence | null
  rule_id?: string | null
}

export interface LLMUsage {
  provider: 'bedrock' | 'featherless' | 'ollama' | 'mock' | 'cache'
  model: string
  input_tokens: number
  output_tokens: number
  cost_usd: number
}

export interface AgentResult {
  agent: AgentName
  status: AgentStatus
  risk?: number | null
  duration_ms: number
  error?: string | null
  findings: Finding[]
  artifacts?: Record<string, string>
  llm_usage?: LLMUsage | null
}

export interface PageInfo { page: number; width: number; height: number }
export interface ExtractedValue { value: unknown; source_text?: string | null }

export interface Document {
  id: string
  type: DocType
  filename: string
  pages: PageInfo[]
  redacted_text?: string | null
  extracted?: Record<string, ExtractedValue> | null
}

export interface ScoreItem {
  code: string
  severity: 'info' | 'low' | 'medium' | 'high' | 'critical'
  weight: number
  message: string
  hard_override?: boolean
}

export interface Verdict {
  risk: number
  label: 'clean' | 'suspicious' | 'forged' | 'identity_fraud' | 'fraud_ring'
  summary: string
  recommendation: 'clear' | 'review' | 'escalate'
  incomplete: boolean
  /** „De ce acest scor”: dovezile cu ponderea lor (noisy-OR). Lipsește în replay-urile vechi. */
  breakdown?: ScoreItem[]
  summary_source?: 'llm' | 'template' | 'template_after_check'
}

export type DecisionAction = 'clear' | 'reject' | 'escalate' | 'flag_network' | 'correct'

export interface Decision {
  action: DecisionAction
  decided_by: string
  notes: string
  corrections: Record<string, unknown>
  decided_at?: string | null
}

export interface Case {
  id: string
  source: 'bank' | 'arena'
  status: CaseStatus
  created_at: string
  requested_amount_ron?: number | null
  applicant_token?: string | null
  documents: Document[]
  fingerprints: Record<string, string[]>
  results: AgentResult[]
  verdict?: Verdict | null
  decision?: Decision | null
}

export interface PipelineEvent {
  case_id: string
  seq: number
  ts: string
  type: EventType
  agent?: AgentName | null
  message: string
  data?: Record<string, unknown> | null
}

export const AGENTS: AgentName[] = ['paznic', 'functionar', 'verificator', 'detector', 'detectiv', 'compliance']
