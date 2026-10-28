import type { AgentName, DecisionAction, DocType, Severity, Verdict } from './types'

export const AGENT_INFO: Record<AgentName, { label: string; icon: string; role: string }> = {
  paznic: { label: 'Paznicul', icon: '🛡️', role: 'ascunde datele personale' },
  functionar: { label: 'Funcționarul', icon: '📄', role: 'extrage datele' },
  verificator: { label: 'Verificatorul', icon: '🔍', role: 'reface calculele' },
  detector: { label: 'Detectorul', icon: '🤖', role: 'caută editări' },
  detectiv: { label: 'Detectivul', icon: '🕵️', role: 'leagă dosarele' },
  compliance: { label: 'Compliance', icon: '⚖️', role: 'dă verdictul' },
}

export const DOC_LABEL: Record<DocType, string> = {
  id_card: 'Buletin',
  payslip: 'Fluturaș de salariu',
  bank_statement: 'Extras de cont',
  employment_certificate: 'Adeverință',
  other: 'Alt document',
  unknown: 'Necunoscut',
}

// Riscul nu e doar culoare: are mereu iconiță + etichetă (proiector, daltonism).
export const SEVERITY: Record<Severity, { label: string; icon: string; cls: string }> = {
  info: { label: 'Info', icon: 'ℹ️', cls: 'bg-slate-100 text-slate-800 border-slate-300' },
  low: { label: 'Scăzut', icon: '▫️', cls: 'bg-sky-50 text-sky-900 border-sky-300' },
  medium: { label: 'Mediu', icon: '⚠️', cls: 'bg-amber-50 text-amber-900 border-amber-400' },
  high: { label: 'Ridicat', icon: '🔶', cls: 'bg-orange-50 text-orange-900 border-orange-500' },
  critical: { label: 'Critic', icon: '⛔', cls: 'bg-red-50 text-red-900 border-red-600' },
}

export function riskLevel(risk: number): { label: string; icon: string; cls: string } {
  if (risk >= 0.8) return { label: 'Risc foarte mare', icon: '⛔', cls: 'text-red-700' }
  if (risk >= 0.5) return { label: 'Risc mare', icon: '🔶', cls: 'text-orange-700' }
  if (risk >= 0.25) return { label: 'Risc moderat', icon: '⚠️', cls: 'text-amber-700' }
  return { label: 'Risc scăzut', icon: '✅', cls: 'text-emerald-700' }
}

export const VERDICT_LABEL: Record<Verdict['label'], string> = {
  clean: 'Fără probleme',
  suspicious: 'Suspect',
  forged: 'Document falsificat',
  identity_fraud: 'Furt de identitate',
  fraud_ring: 'Rețea de fraudă',
}

export const RECOMMENDATION_LABEL: Record<Verdict['recommendation'], string> = {
  clear: 'Aprobare',
  review: 'Verificare manuală',
  escalate: 'Investigație',
}

export const DECISION_LABEL: Record<DecisionAction, string> = {
  clear: 'Aprobă',
  reject: 'Respinge',
  escalate: 'Trimite la investigație',
  flag_network: 'Marchează rețeaua',
  correct: 'Corectează',
}
