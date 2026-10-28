import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getSettings, setLlmMode, type LlmMode } from '@/lib/api'
import { cn } from '@/lib/utils'

const PREV_KEY = 'orb.prevLlmMode'
const LABEL: Record<LlmMode, string> = {
  bedrock: '☁️ Claude (cloud)', cloud: '☁️ Featherless (cloud)', local: '🔒 100% local', mock: '🧪 mock',
}

/** Butonul „mod 100% local”: tot AI-ul rulează pe serverul băncii, fără internet. */
export function LocalModeToggle() {
  const qc = useQueryClient()
  const q = useQuery({ queryKey: ['settings'], queryFn: getSettings, refetchInterval: 15000 })
  const m = useMutation({
    mutationFn: setLlmMode,
    onSuccess: (s) => qc.setQueryData(['settings'], s),
  })
  const mode = q.data?.llm_mode
  if (!mode) return null
  const local = mode === 'local'

  function toggle() {
    if (local) {
      let prev: LlmMode = 'bedrock'
      try { prev = (sessionStorage.getItem(PREV_KEY) as LlmMode) || 'bedrock' } catch { /* mod privat */ }
      m.mutate(prev === 'local' ? 'bedrock' : prev)
    } else {
      try { sessionStorage.setItem(PREV_KEY, mode!) } catch { /* mod privat */ }
      m.mutate('local')
    }
  }

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={m.isPending}
      aria-pressed={local}
      title="Comută între AI-ul din cloud și AI-ul local (fără internet)"
      className={cn('rounded-full border px-4 py-1.5 text-base font-semibold transition-colors disabled:opacity-60',
        local ? 'border-emerald-400 bg-emerald-500/20 text-emerald-200' : 'border-slate-600 text-slate-200 hover:bg-white/10')}
    >
      {m.isPending ? 'se schimbă…' : LABEL[mode]}
      {!local && <span className="ml-2 text-slate-400">→ trece pe 🔒 local</span>}
    </button>
  )
}
