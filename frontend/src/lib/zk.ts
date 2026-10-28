import { apiFetch, ApiError } from './api'

// Dovada „venit net ≥ prag” (ZK): totul rulează pe backend prin POST /api/zk/demo.
// Banca nu vede salariul; vede doar angajamentul semnat de angajator și dovada.

export type ZkAttack = 'none' | 'lie_salary' | 'lower_threshold' | 'fake_signature' | 'replay'

export interface ZkDemoRequest {
  net_salary_ron: number
  installment_ron: number
  cui: string
  period: string
  attack: ZkAttack
}

export interface ZkStep {
  actor: string
  action: string
  detail: string
}

export interface ZkDemoResult {
  ok: boolean
  answer: 'DA' | 'NU'
  reason: string
  attack: ZkAttack
  steps: ZkStep[]
  employer?: string | null
  threshold_ron?: number
  installment_ron?: number
  verify_ms?: number
  /** Tot ce primește banca: fără salariu, fără sare. */
  bank_saw?: { cui: string; period: string; commitment: string; nonce?: string; proof_bytes: number }
}

export const DSTI = 0.4

export const ATTACKS: { id: ZkAttack; label: string; hint: string }[] = [
  { id: 'none', label: 'Fără atac', hint: 'Clientul cinstit dovedește venitul atestat.' },
  { id: 'lie_salary', label: 'Minte la salariu', hint: 'Pretinde un salariu mai mare decât cel semnat de angajator.' },
  { id: 'lower_threshold', label: 'Coboară pragul', hint: 'Dovedește un prag mai mic decât cel cerut de bancă.' },
  { id: 'fake_signature', label: 'Semnătură falsă', hint: 'Semnează singur atestarea, cu o cheie din afara registrului.' },
  { id: 'replay', label: 'Retrimite dovada', hint: 'Folosește a doua oară o dovadă deja acceptată.' },
]

// Firmele inventate din Arenă (aceleași CUI-uri ca în registrul angajatorilor de pe backend).
export const EMPLOYERS: { cui: string; name: string }[] = [
  { cui: 'RO9341910290', name: 'Bitwave Software SRL' },
  { cui: 'RO9185472906', name: 'Tehnoserv Construct SRL' },
  { cui: 'RO9477321003', name: 'Nordic Consulting Grup SRL' },
  { cui: 'RO9402119372', name: 'Agro Prahova Distribuție SRL' },
]

export async function runZkDemo(body: ZkDemoRequest): Promise<ZkDemoResult> {
  try {
    const res = await apiFetch('/api/zk/demo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': '1' },
      body: JSON.stringify(body),
    })
    return res.json()
  } catch (e) {
    if (e instanceof ApiError) throw new Error(errorMessage(e.status))
    throw new Error('Serverul nu răspunde. Verifică backend-ul sau deschide pagina cu ?mock=1.')
  }
}

function errorMessage(status: number): string {
  if (status === 503) return 'ZK nu e disponibil pe acest server: lipsesc nargo/bb (vezi zk/README.md). Pentru demo, folosește ?mock=1.'
  if (status === 404) return 'Angajatorul nu e în registru.'
  if (status === 422) return 'Datele din formular nu sunt valide.'
  return `Cererea a eșuat (${status}).`
}

/** Același flux ca pe backend, cu valori inventate, pentru demo fără server (?mock=1). */
export function mockZkDemo(body: ZkDemoRequest): ZkDemoResult {
  const threshold = Math.round((body.installment_ron / DSTI) * 100) / 100
  const employer = EMPLOYERS.find((e) => e.cui === body.cui)?.name ?? null
  const fmt = (n: number) => n.toFixed(2)
  const commitment = '0x1c3f9a52e07b4d18a6e2c9f05b7d3e41a8c6f2b90d4e7a15c3b8f60e92d4a7b1'
  const proofBytes = 14_592
  const steps: ZkStep[] = [
    { actor: 'bancă', action: 'cere dovadă', detail: `rată ${fmt(body.installment_ron)} lei → prag ${fmt(threshold)} lei, nonce unic` },
    { actor: 'angajator', action: 'atestă', detail: 'angajament + semnătură ECDSA (salariul merge doar la client)' },
  ]
  const base = { employer, threshold_ron: threshold, installment_ron: body.installment_ron, attack: body.attack, verify_ms: 41 }
  const no = (reason: string): ZkDemoResult => ({ ...base, ok: false, answer: 'NU', reason, steps })

  // Ca în circuit: clientul nu poate genera dovada dacă afirmația e falsă.
  const proven = body.attack === 'lower_threshold' ? threshold / 2 : threshold
  if (body.attack === 'lie_salary' || body.net_salary_ron < proven) {
    const reason = 'circuitul refuză: salariul nu corespunde angajamentului sau e sub prag'
    steps.push({ actor: 'client', action: 'nu poate genera dovada', detail: reason })
    return no(`clientul nu poate dovedi: ${reason}`)
  }
  steps.push({ actor: 'client', action: 'generează dovada', detail: `${proofBytes} octeți în 1840 ms` })
  const bank_saw = { cui: body.cui, period: body.period, commitment, proof_bytes: proofBytes }

  let res: ZkDemoResult
  if (body.attack === 'lower_threshold') res = no('dovada ZK nu e validă pentru pragul și cererea băncii')
  else if (body.attack === 'fake_signature') res = no('semnătura angajatorului nu e validă')
  else res = { ...base, ok: true, answer: 'DA', reason: 'venit net ≥ prag, atestat de angajator; salariul nu a fost văzut', steps }
  steps.push({ actor: 'bancă', action: 'verifică', detail: `${res.answer} — ${res.reason}` })

  if (body.attack === 'replay') {
    res = no('nonce necunoscut, expirat sau deja folosit')
    steps.push({ actor: 'atacator', action: 'retrimite aceeași dovadă', detail: `NU — ${res.reason}` })
  }
  return { ...res, steps, bank_saw }
}
