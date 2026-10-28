import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Cloud, HardDrive } from 'lucide-react'
import { getSettings, setLlmMode, type LlmMode } from '@/lib/api'
import { cn } from '@/lib/utils'

const PREV_KEY = 'orb.prevLlmMode'

/** „Mod 100% local”: tot AI-ul rulează pe serverul băncii, fără internet. Comutator în două poziții. */
export function LocalModeToggle() {
  const qc = useQueryClient()
  const q = useQuery({ queryKey: ['settings'], queryFn: getSettings, refetchInterval: 15000 })
  const m = useMutation({ mutationFn: setLlmMode, onSuccess: (s) => qc.setQueryData(['settings'], s) })
  const mode = q.data?.llm_mode
  if (!mode) return null
  const local = mode === 'local'

  function choose(wantLocal: boolean) {
    if (wantLocal === local || m.isPending) return
    if (wantLocal) {
      try { sessionStorage.setItem(PREV_KEY, mode!) } catch { /* mod privat */ }
      m.mutate('local')
    } else {
      let prev: LlmMode = 'bedrock'
      try { prev = (sessionStorage.getItem(PREV_KEY) as LlmMode) || 'bedrock' } catch { /* mod privat */ }
      m.mutate(prev === 'local' ? 'bedrock' : prev)
    }
  }

  const seg = (on: boolean) => cn(
    'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium transition-colors',
    on ? 'bg-ink text-white' : 'text-ink-2 hover:text-ink',
  )
  return (
    <div role="group" aria-label="Where the AI runs" className="flex items-center gap-2">
      <span className="hidden text-sm text-ink-3 lg:inline">AI</span>
      <div className="flex overflow-hidden rounded-sm border border-line">
        <button type="button" className={seg(!local)} aria-pressed={!local} onClick={() => choose(false)}
                title={mode === 'mock' ? 'Saved responses (test)' : 'Cloud models, receive only pseudonymized data'}>
          <Cloud className="h-4 w-4" aria-hidden /> {mode === 'mock' ? 'Test' : 'Cloud'}
        </button>
        <button type="button" className={seg(local)} aria-pressed={local} onClick={() => choose(true)}
                title="Everything runs on the bank's server, no internet">
          <HardDrive className="h-4 w-4" aria-hidden /> Local
        </button>
      </div>
    </div>
  )
}
