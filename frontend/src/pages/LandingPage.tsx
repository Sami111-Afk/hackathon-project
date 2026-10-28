import { ArrowRight, FileText, IdCard, Landmark, Lock, ScrollText, Server } from 'lucide-react'
import { CtaButton } from '@/components/landing/CtaButton'
import { FeatureCard } from '@/components/landing/FeatureCard'
import { HeroPreview } from '@/components/landing/HeroPreview'
import { LandingFooter } from '@/components/landing/LandingFooter'
import { LandingNav } from '@/components/landing/LandingNav'
import { Section } from '@/components/landing/Section'
import { StatBand } from '@/components/landing/StatBand'
import { StepList } from '@/components/landing/StepList'
import { usePageMeta } from '@/hooks/usePageMeta'
import { AGENT_INFO } from '@/lib/labels'
import type { AgentName } from '@/lib/types'

const DEMO_CASE = '/cases/case_maria?mock=1' // merge fără cont și fără backend (datele demo ale Mariei)

const AGENTS: [AgentName, string][] = [
  ['paznic', 'Before any AI sees a document, names, CNP, IBAN, phone numbers and addresses become labels like [PERSOANA_1]. Blurry photos and ID cards never go to the cloud.'],
  ['functionar', 'Reads the ID card, payslip and bank statement and turns them into fields: employer, gross and net pay, monthly income.'],
  ['verificator', 'Recomputes the net pay from the gross with Romanian tax rules and checks that the employer is active in the ANAF registry (a demo registry for this demo's fictional companies).'],
  ['detector', 'Looks for signs of editing in the scans and PDFs: image analysis of edited areas, PDF edit traces, metadata.'],
  ['detectiv', 'Compares phone, IBAN and address with other applications, to find one person applying under several identities.'],
  ['compliance', 'Weighs all the evidence into a risk level and a recommendation. Every point is marked on the document.'],
]

const STEPS = [
  { title: 'Upload', text: 'The analyst uploads the ID card, payslip and bank statement: scans or phone photos.' },
  { title: 'Hide personal data', text: 'The Guard swaps personal data for labels. The AI sees [PERSOANA_1], never the name.' },
  { title: 'Check', text: 'The agents read, recompute, check ANAF, and look for edits and links to other applications.' },
  { title: 'Decide', text: 'The analyst gets a risk level with the evidence marked on each document, and decides with all the evidence in front of them.' },
]

// Cifre măsurate: scripts/benchmark_pipeline.py --n 60 --llm bedrock (data/benchmark/pipeline_results.json, clean_bedrock).
const STATS = [
  { value: '0', label: 'personal data values sent to the cloud AI', note: '60 applications with the real model; also 0 on 20 phone photos' },
  { value: '36/36', label: 'forged applications flagged', note: 'edited net pay, edited balance, inactive employer' },
  { value: '0/12', label: 'honest applicants accused of fraud', note: '3 of the 12 were sent to a human for a second look' },
  { value: '~12 s', label: 'per application, cloud AI', note: '8–9 s fully local, on a laptop GPU' },
]

const PRIVACY = [
  { icon: Lock, text: 'The cloud AI only ever sees labels, never names or ID numbers.' },
  { icon: ScrollText, text: 'Every AI call is written to an audit log: what was sent, and where.' },
  { icon: Server, text: 'Local mode: everything runs on the bank\'s own machine, with no internet.' },
]

const REDACT: [string, string, string][] = [
  ['Name', 'Maria Ionescu', '[PERSOANA_1]'],
  ['CNP', '2850412******', '[CNP_1]'],
  ['IBAN', 'RO49 AAAA 1B31 0075 9384 0000', '[IBAN_1]'],
  ['Phone', '0722 123 456', '[TELEFON_1]'],
  ['Address', 'Str. Florilor 12, Cluj', '[ADRESA_1]'],
]

/** Pagina publică de prezentare ORB (`/`): ce face, cum, cifrele măsurate; de aici spre Arena și demo. */
export function LandingPage() {
  usePageMeta('ORB: loan documents checked in seconds, personal data stays at the bank',
    'AI agents check the ID card, payslip and bank statement of every loan application. The analyst sees the evidence and decides; personal data never reaches the cloud AI.')
  return (
    <div className="landing min-h-dvh bg-night text-night-ink">
      <a href="#main" className="sr-only z-50 rounded-sm bg-brand px-4 py-2 font-semibold text-ink focus:not-sr-only focus:fixed focus:left-4 focus:top-4">Skip to content</a>
      <div className="h-1 bg-brand" />
      <LandingNav />
      <main id="main">
        {/* Hero: fără animație de intrare (ar întârzia LCP-ul) */}
        <section className="relative overflow-hidden px-4 pb-20 pt-14 sm:px-6 lg:px-8 lg:pb-28 lg:pt-20">
          <div className="pointer-events-none absolute -top-40 left-1/2 h-[36rem] w-[36rem] -translate-x-1/2 rounded-full bg-brand/5 blur-3xl" aria-hidden />
          <div className="relative mx-auto grid max-w-6xl grid-cols-1 items-center gap-14 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-night-line px-3.5 py-1.5 text-sm font-medium text-night-mute">
                <span className="h-2 w-2 rounded-full bg-brand" aria-hidden />For bank credit teams
              </p>
              <h1 className="mt-6 text-5xl font-bold leading-[1.04] tracking-tight sm:text-display">
                Loan files checked in <span className="text-brand">seconds</span>, not ~20&nbsp;minutes
              </h1>
              <p className="mt-6 max-w-xl text-lg leading-relaxed text-night-mute sm:text-xl">
                AI agents read the ID card, payslip and bank statement, redo the tax math, check the employer and look for edits.
                The analyst sees the evidence and decides. Personal data never reaches the cloud AI.
              </p>
              <div className="mt-9 flex flex-wrap gap-3">
                <CtaButton to="/arena">Try the Arena</CtaButton>
                <CtaButton to={DEMO_CASE} variant="outline">See a demo case</CtaButton>
              </div>
              <p className="mt-10 flex items-baseline gap-3 border-t border-night-line pt-6">
                <span className="font-condensed text-5xl font-bold leading-none text-brand">0</span>
                <span className="text-night-mute">personal data values sent to the cloud AI, measured on 60 test applications</span>
              </p>
            </div>
            <HeroPreview />
          </div>
        </section>

        <Section id="problem" eyebrow="The problem" title="An analyst spends roughly 20 minutes on every application (our estimate)"
          intro="Read the ID card, recompute the taxes on the payslip, look the employer up at ANAF, compare it all with the bank statement. It is repetitive and slow, a well-made fake still slips through, and nobody checks whether the same phone number is on five other applications."
          className="bg-night-2/40">
          <div className="reveal relative mx-auto mt-16 flex h-64 max-w-lg items-center justify-center" aria-hidden>
            {[{ icon: IdCard, label: 'ID card', rot: '-rotate-8 -translate-x-20 sm:-translate-x-28' }, { icon: FileText, label: 'Payslip', rot: 'z-10 -translate-y-3' }, { icon: Landmark, label: 'Bank statement', rot: 'rotate-8 translate-x-20 sm:translate-x-28' }].map((d) => (
              <div key={d.label} className={`absolute w-40 rounded-xl bg-surface p-4 text-ink shadow-xl ring-1 ring-black/5 sm:w-52 ${d.rot}`}>
                <d.icon className="h-5 w-5 text-ink-2" />
                <div className="mt-2 text-sm font-semibold">{d.label}</div>
                <div className="mt-3 space-y-1.5">
                  <div className="h-2 w-full rounded-full bg-canvas" /><div className="h-2 w-4/5 rounded-full bg-canvas" /><div className="h-2 w-3/5 rounded-full bg-canvas" />
                </div>
              </div>
            ))}
          </div>
        </Section>

        <Section id="agents" eyebrow="The agents" title="Six agents, one job each"
          intro="Each agent checks one thing and shows its evidence. None of them makes the decision.">
          <div className="mt-14 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {AGENTS.map(([name, text]) => {
              const a = AGENT_INFO[name]
              return <FeatureCard key={name} icon={a.icon} title={a.label} role={a.role} text={text} />
            })}
          </div>
        </Section>

        <Section id="how" eyebrow="How it works" title="From upload to decision in four steps" className="bg-night-2/40">
          <StepList steps={STEPS} />
        </Section>

        <Section id="results" eyebrow="Results" title="Measured, not estimated"
          intro="A benchmark of generated loan applications, run through the full pipeline with the real cloud model (Claude Haiku on Amazon Bedrock). Synthetic data, and the forgeries are ours: it shows the pipeline is correct on the cases we designed, not accuracy on real-world fraud.">
          <StatBand stats={STATS} />
          <p className="reveal mt-6 max-w-3xl text-sm leading-relaxed text-night-mute">
            Known limit, said openly: a fake that is perfect on paper still passes 9 times out of 12. Catching it needs the bank&apos;s own
            statement data, so ORB flags what it can prove and sends unclear applications to a human instead of guessing.
          </p>
        </Section>

        <Section id="privacy" className="bg-night-2/40">
          <div className="grid grid-cols-1 items-center gap-14 lg:grid-cols-2">
            <div className="reveal">
              <p className="text-sm font-semibold uppercase tracking-[0.14em] text-brand">Privacy</p>
              <h2 id="privacy-title" className="mt-3 text-4xl font-bold tracking-tight sm:text-display-sm">Personal data stays at the bank</h2>
              <ul className="mt-8 space-y-5">
                {PRIVACY.map((p) => (
                  <li key={p.text} className="flex gap-4">
                    <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-night-line text-brand"><p.icon className="h-5 w-5" aria-hidden /></span>
                    <span className="pt-2 text-lg leading-relaxed text-night-mute">{p.text}</span>
                  </li>
                ))}
              </ul>
            </div>
            <figure className="reveal overflow-hidden rounded-2xl border border-night-line bg-night">
              <figcaption className="flex items-center justify-between border-b border-night-line px-5 py-3.5 text-sm">
                <span className="font-semibold">What the cloud AI sees</span><span className="text-night-mute">fictional example</span>
              </figcaption>
              <table className="w-full text-left text-[15px]">
                <thead className="sr-only"><tr><th>Field</th><th>In the document</th><th>Sent to the AI</th></tr></thead>
                <tbody className="divide-y divide-night-line">
                  {REDACT.map(([field, before, after]) => (
                    <tr key={field}>
                      <th scope="row" className="w-24 px-5 py-3.5 font-medium text-night-mute">{field}</th>
                      <td className="px-2 py-3.5 text-night-mute line-through decoration-night-danger/70">{before}</td>
                      <td className="py-3.5 pr-5 text-right"><ArrowRight className="mr-2 inline h-4 w-4 text-night-mute" aria-hidden /><code className="rounded-sm bg-brand/15 px-1.5 py-0.5 font-mono text-sm text-brand">{after}</code></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </figure>
          </div>
        </Section>

        <section aria-labelledby="cta-title" className="px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
          <div className="reveal mx-auto max-w-6xl rounded-[2rem] bg-brand px-6 py-16 text-center text-ink sm:px-12 lg:py-20">
            <h2 id="cta-title" className="mx-auto max-w-3xl text-4xl font-bold tracking-tight sm:text-display-sm">Can you fool the agents?</h2>
            <p className="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-ink/75">Forge a payslip on your phone and see whether ORB catches it. One minute, no account.</p>
            <div className="mt-9 flex flex-wrap justify-center gap-3">
              <CtaButton to="/arena" variant="dark">Play the Arena</CtaButton>
              <CtaButton to={DEMO_CASE} variant="outline-dark">See Maria&apos;s application</CtaButton>
            </div>
          </div>
        </section>
      </main>
      <LandingFooter />
    </div>
  )
}
