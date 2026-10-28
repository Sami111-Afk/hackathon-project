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
  answer: 'DA' | 'NU' | 'YES' | 'NO' // valoare-mașină DA/NU; afișată ca YES/NO
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
  { id: 'none', label: 'No attack', hint: 'The honest client proves the attested income.' },
  { id: 'lie_salary', label: 'Lies about salary', hint: 'Claims a higher salary than the one signed by the employer.' },
  { id: 'lower_threshold', label: 'Lower the threshold', hint: 'Proves a lower threshold than the one the bank asked for.' },
  { id: 'fake_signature', label: 'Fake signature', hint: 'Signs the attestation itself, with a key from outside the registry.' },
  { id: 'replay', label: 'Replay the proof', hint: 'Reuses a proof that was already accepted.' },
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
    throw new Error('The server is not responding. Check the backend or open the page with ?mock=1.')
  }
}

function errorMessage(status: number): string {
  if (status === 503) return 'ZK is not available on this server: nargo/bb are missing (see zk/README.md). For the demo, use ?mock=1.'
  if (status === 404) return 'The employer is not in the registry.'
  if (status === 422) return 'The form data is not valid.'
  return `The request failed (${status}).`
}

/** Același flux ca pe backend, cu valori inventate, pentru demo fără server (?mock=1). */
export function mockZkDemo(body: ZkDemoRequest): ZkDemoResult {
  const threshold = Math.round((body.installment_ron / DSTI) * 100) / 100
  const employer = EMPLOYERS.find((e) => e.cui === body.cui)?.name ?? null
  const fmt = (n: number) => n.toFixed(2)
  const commitment = '0x1c3f9a52e07b4d18a6e2c9f05b7d3e41a8c6f2b90d4e7a15c3b8f60e92d4a7b1'
  const proofBytes = 14_592
  const steps: ZkStep[] = [
    { actor: 'bank', action: 'requests proof', detail: `installment ${fmt(body.installment_ron)} lei → threshold ${fmt(threshold)} lei, unique nonce` },
    { actor: 'employer', action: 'attests', detail: 'commitment + ECDSA signature (the salary goes only to the client)' },
  ]
  const base = { employer, threshold_ron: threshold, installment_ron: body.installment_ron, attack: body.attack, verify_ms: 41 }
  const no = (reason: string): ZkDemoResult => ({ ...base, ok: false, answer: 'NU', reason, steps })

  // Ca în circuit: clientul nu poate genera dovada dacă afirmația e falsă.
  const proven = body.attack === 'lower_threshold' ? threshold / 2 : threshold
  if (body.attack === 'lie_salary' || body.net_salary_ron < proven) {
    const reason = 'the circuit refuses: the salary does not match the commitment or is below the threshold'
    steps.push({ actor: 'customer', action: 'cannot generate proof', detail: reason })
    return no(`the client cannot prove it: ${reason}`)
  }
  steps.push({ actor: 'customer', action: 'generates proof', detail: `${proofBytes} bytes in 1840 ms` })
  const bank_saw = { cui: body.cui, period: body.period, commitment, proof_bytes: proofBytes }

  let res: ZkDemoResult
  if (body.attack === 'lower_threshold') res = no('the ZK proof is not valid for the bank\'s threshold and request')
  else if (body.attack === 'fake_signature') res = no('the employer\'s signature is not valid')
  else res = { ...base, ok: true, answer: 'DA', reason: 'net income ≥ threshold, attested by the employer; the salary was never seen', steps }
  steps.push({ actor: 'bank', action: 'verifies', detail: `${normAnswer(res.answer)} — ${res.reason}` })

  if (body.attack === 'replay') {
    res = no('nonce unknown, expired or already used')
    steps.push({ actor: 'attacker', action: 'resends the same proof', detail: `NO — ${res.reason}` })
  }
  return { ...res, steps, bank_saw }
}

// Backend-ul poate trimite încă text românesc (DA/NU, actori, motive); îl afișăm în engleză.
const ACTOR_EN: Record<string, string> = { 'bancă': 'bank', angajator: 'employer', client: 'customer', atacator: 'attacker' }
export const normActor = (a: string) => ACTOR_EN[a] ?? a
export const normAnswer = (a: string) => (a === 'DA' ? 'YES' : a === 'NU' ? 'NO' : a)
const REASON_EN: Record<string, string> = {
  'venit net ≥ prag, atestat de angajator; salariul nu a fost văzut': 'net income ≥ threshold, attested by the employer; the salary was never seen',
  'semnătura angajatorului nu e validă': "the employer's signature is not valid",
  'nonce necunoscut, expirat sau deja folosit': 'nonce unknown, expired or already used',
}
export const normText = (t: string) => REASON_EN[t] ?? t
