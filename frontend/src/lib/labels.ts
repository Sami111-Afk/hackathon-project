import {
  AlertOctagon, AlertTriangle, Calculator, CheckCircle2, FileText, Info, Minus, Network, Scale, ScanSearch,
  ShieldCheck, type LucideIcon,
} from 'lucide-react'
import type { AgentName, DecisionAction, DocType, Severity, Verdict } from './types'

export const AGENT_INFO: Record<AgentName, { label: string; icon: LucideIcon; role: string }> = {
  paznic: { label: 'Paznicul', icon: ShieldCheck, role: 'Ascunde datele personale' },
  functionar: { label: 'Funcționarul', icon: FileText, role: 'Extrage datele din acte' },
  verificator: { label: 'Verificatorul', icon: Calculator, role: 'Reface calculele, verifică ANAF' },
  detector: { label: 'Detectorul', icon: ScanSearch, role: 'Caută editări și imagini AI' },
  detectiv: { label: 'Detectivul', icon: Network, role: 'Leagă dosarul de alte cereri' },
  compliance: { label: 'Compliance', icon: Scale, role: 'Cântărește dovezile' },
}

export const DOC_LABEL: Record<DocType, string> = {
  id_card: 'Buletin',
  payslip: 'Fluturaș de salariu',
  bank_statement: 'Extras de cont',
  employment_certificate: 'Adeverință',
  other: 'Alt document',
  unknown: 'Necunoscut',
}

// Gravitatea nu e doar culoare: are mereu iconiță + cuvânt (proiector, daltonism).
export const SEVERITY: Record<Severity, { label: string; icon: LucideIcon; text: string; bg: string; bar: string }> = {
  info: { label: 'Info', icon: Info, text: 'text-ink-2', bg: 'bg-canvas', bar: 'bg-ink-3' },
  low: { label: 'Scăzut', icon: Minus, text: 'text-ink-2', bg: 'bg-canvas', bar: 'bg-ink-3' },
  medium: { label: 'Mediu', icon: AlertTriangle, text: 'text-warn', bg: 'bg-warn-bg', bar: 'bg-warn' },
  high: { label: 'Ridicat', icon: AlertTriangle, text: 'text-danger', bg: 'bg-danger-bg', bar: 'bg-danger' },
  critical: { label: 'Critic', icon: AlertOctagon, text: 'text-danger', bg: 'bg-danger-bg', bar: 'bg-danger' },
}

export function riskLevel(risk: number): { label: string; icon: LucideIcon; text: string; bar: string } {
  if (risk >= 0.8) return { label: 'Risc foarte mare', icon: AlertOctagon, text: 'text-danger', bar: 'bg-danger' }
  if (risk >= 0.5) return { label: 'Risc mare', icon: AlertTriangle, text: 'text-danger', bar: 'bg-danger' }
  if (risk >= 0.25) return { label: 'Risc moderat', icon: AlertTriangle, text: 'text-warn', bar: 'bg-warn' }
  return { label: 'Risc scăzut', icon: CheckCircle2, text: 'text-ok', bar: 'bg-ok' }
}

export const VERDICT_LABEL: Record<Verdict['label'], string> = {
  clean: 'Fără probleme',
  suspicious: 'Suspect',
  forged: 'Document falsificat',
  identity_fraud: 'Furt de identitate',
  fraud_ring: 'Rețea de fraudă',
}

export const RECOMMENDATION_LABEL: Record<Verdict['recommendation'], string> = {
  clear: 'aprobare',
  review: 'verificare manuală',
  escalate: 'investigație de fraudă',
}

export const DECISION_LABEL: Record<DecisionAction, string> = {
  clear: 'Aprobă cererea',
  reject: 'Respinge cererea',
  escalate: 'Trimite la investigație',
  flag_network: 'Marchează rețeaua',
  correct: 'Corectează',
}

export const DECISION_DONE: Record<DecisionAction, string> = {
  clear: 'Cerere aprobată',
  reject: 'Cerere respinsă',
  escalate: 'Trimisă la investigație',
  flag_network: 'Rețea marcată',
  correct: 'Corectat',
}
