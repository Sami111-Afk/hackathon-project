import {
  AlertOctagon, AlertTriangle, Calculator, CheckCircle2, FileText, Info, Minus, Network, Scale, ScanSearch,
  ShieldCheck, type LucideIcon,
} from 'lucide-react'
import type { AgentName, DecisionAction, DocType, Severity, Verdict } from './types'

export const AGENT_INFO: Record<AgentName, { label: string; icon: LucideIcon; role: string }> = {
  paznic: { label: 'Guard', icon: ShieldCheck, role: 'Hides personal data' },
  functionar: { label: 'Clerk', icon: FileText, role: 'Extracts data from documents' },
  verificator: { label: 'Verifier', icon: Calculator, role: 'Redoes the math, checks ANAF' },
  detector: { label: 'Detector', icon: ScanSearch, role: 'Looks for edits and AI images' },
  detectiv: { label: 'Detective', icon: Network, role: 'Links the application to other requests' },
  compliance: { label: 'Compliance', icon: Scale, role: 'Weighs the evidence' },
}

export const DOC_LABEL: Record<DocType, string> = {
  id_card: 'ID card',
  payslip: 'Payslip',
  bank_statement: 'Bank statement',
  employment_certificate: 'Employment certificate',
  other: 'Other document',
  unknown: 'Unknown',
}

// Gravitatea nu e doar culoare: are mereu iconiță + cuvânt (proiector, daltonism).
export const SEVERITY: Record<Severity, { label: string; icon: LucideIcon; text: string; bg: string; bar: string }> = {
  info: { label: 'Info', icon: Info, text: 'text-ink-2', bg: 'bg-canvas', bar: 'bg-ink-3' },
  low: { label: 'Low', icon: Minus, text: 'text-ink-2', bg: 'bg-canvas', bar: 'bg-ink-3' },
  medium: { label: 'Medium', icon: AlertTriangle, text: 'text-warn', bg: 'bg-warn-bg', bar: 'bg-warn' },
  high: { label: 'High', icon: AlertTriangle, text: 'text-danger', bg: 'bg-danger-bg', bar: 'bg-danger' },
  critical: { label: 'Critical', icon: AlertOctagon, text: 'text-danger', bg: 'bg-danger-bg', bar: 'bg-danger' },
}

export function riskLevel(risk: number): { label: string; icon: LucideIcon; text: string; bar: string } {
  if (risk >= 0.8) return { label: 'Very high risk', icon: AlertOctagon, text: 'text-danger', bar: 'bg-danger' }
  if (risk >= 0.5) return { label: 'High risk', icon: AlertTriangle, text: 'text-danger', bar: 'bg-danger' }
  if (risk >= 0.25) return { label: 'Moderate risk', icon: AlertTriangle, text: 'text-warn', bar: 'bg-warn' }
  return { label: 'Low risk', icon: CheckCircle2, text: 'text-ok', bar: 'bg-ok' }
}

export const VERDICT_LABEL: Record<Verdict['label'], string> = {
  clean: 'No issues',
  suspicious: 'Suspicious',
  forged: 'Forged document',
  identity_fraud: 'Identity theft',
  fraud_ring: 'Fraud ring',
}

export const RECOMMENDATION_LABEL: Record<Verdict['recommendation'], string> = {
  clear: 'approval',
  review: 'manual review',
  escalate: 'fraud investigation',
}

export const DECISION_LABEL: Record<DecisionAction, string> = {
  clear: 'Approve application',
  reject: 'Reject application',
  escalate: 'Send to investigation',
  flag_network: 'Flag the ring',
  correct: 'Correct',
}

export const DECISION_DONE: Record<DecisionAction, string> = {
  clear: 'Application approved',
  reject: 'Application rejected',
  escalate: 'Sent to investigation',
  flag_network: 'Ring flagged',
  correct: 'Corrected',
}
