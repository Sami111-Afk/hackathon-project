import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, type Plugin } from 'vite'

// Pagina fiecărei rute (ține-o în sincron cu App.tsx). Fără asta, telefonul descarcă întâi index.js
// și abia apoi află ce pagină îi trebuie: o călătorie în plus pe rețea, ~1 s pe 4G.
// Al treilea câmp: ruta e după RequireAuth (fără token, routerul trimite la /login).
const ROUTE_PAGES: [RegExp, string, auth?: boolean][] = [
  [/^\/arena\/?$/, 'pages/arena/ArenaStart.tsx'],
  [/^\/arena\/m\//, 'pages/arena/ArenaForge.tsx'],
  [/^\/arena\/r\//, 'pages/arena/ArenaResult.tsx'],
  [/^\/arena\/top/, 'pages/arena/ArenaTop.tsx'],
  [/^\/arena\/live/, 'pages/arena/ArenaLive.tsx'],
  [/^\/login/, 'pages/LoginPage.tsx'],
  [/^\/zk/, 'pages/ZkPage.tsx', true],
  [/^\/cases\//, 'pages/CasePage.tsx', true],
  [/^\/dashboard/, 'pages/DashboardPage.tsx', true],
  [/^\/$/, 'pages/LandingPage.tsx'],
]
// Textul de bază: fără preload, fontul se descoperă abia după ce CSS-ul e citit.
const PRELOAD_FONTS = [/ibm-plex-sans-latin-400-normal-.*\.woff2$/, /ibm-plex-sans-latin-ext-400-normal-.*\.woff2$/]

/** Pune în index.html un script mic care preîncarcă pagina rutei curente + fonturile de bază. */
function routePreload(): Plugin {
  let base = '/'
  return {
    name: 'route-preload',
    apply: 'build',
    configResolved(config) { base = config.base },
    transformIndexHtml: {
      order: 'post',
      handler(html, ctx) {
        if (!ctx.bundle) return html
        const items = Object.values(ctx.bundle)
        const chunks = items.flatMap((c) => (c.type === 'chunk' ? [c] : []))
        const byFile = new Map(chunks.map((c) => [c.fileName, c]))
        const entry = chunks.find((c) => c.isEntry)!
        const loaded = new Set([entry.fileName, ...entry.imports]) // Vite le preîncarcă deja
        const deps = (file: string, out = new Set<string>()): Set<string> => {
          if (loaded.has(file) || out.has(file)) return out
          out.add(file)
          for (const f of byFile.get(file)?.imports ?? []) deps(f, out)
          return out
        }
        const files = (page: string) => {
          const chunk = chunks.find((c) => c.facadeModuleId?.endsWith('/src/' + page))
          if (!chunk) throw new Error(`route-preload: nu găsesc chunk-ul pentru ${page}`)
          return [...deps(chunk.fileName)].map((f) => base + f)
        }
        const routes = ROUTE_PAGES.map(([re, page, auth]) => [re.source, files(page), auth ? 1 : 0])
        // Aceeași regulă ca RequireAuth: token în sessionStorage (lib/auth.ts) sau mod mock (lib/config.ts).
        const script = `<script>(function(){var R=${JSON.stringify(routes)},L=${JSON.stringify(files('pages/LoginPage.tsx'))},p=location.pathname,ok=false;`
          + `try{var q=new URLSearchParams(location.search).get('mock');ok=!!sessionStorage.getItem('orb.token')||(q!==null?q!=='0':sessionStorage.getItem('orb.mock')==='1')}catch(e){}`
          + `for(var i=0;i<R.length;i++)if(new RegExp(R[i][0]).test(p)){(R[i][2]&&!ok?L:R[i][1]).forEach(function(f){var l=document.createElement('link');l.rel='modulepreload';l.href=f;document.head.appendChild(l)});break}})()</script>`
        const fonts = items
          .filter((a) => a.type === 'asset' && PRELOAD_FONTS.some((re) => re.test(a.fileName)))
          .map((a) => `<link rel="preload" href="${base}${a.fileName}" as="font" type="font/woff2" crossorigin>`)
        // CSS-ul (~11 KB gzip) direct în pagină: primul ecran nu mai așteaptă o cerere separată (~150 ms pe 4G).
        for (const a of items) {
          if (a.type !== 'asset' || !a.fileName.endsWith('.css')) continue
          const tag = new RegExp(`<link rel="stylesheet"[^>]*href="${base}${a.fileName}"[^>]*>`)
          html = html.replace(tag, () => `<style>${String(a.source)}</style>`)
        }
        // După <meta charset>: browserul îl caută în primii 1024 de octeți ai paginii.
        return html.replace(/(<meta charset[^>]*>)/, `$1\n    ${script}\n    ${fonts.join('\n    ')}`)
      },
    },
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss(), routePreload()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
      '@shared': path.resolve(import.meta.dirname, '../shared'),
    },
  },
  // fixture-urile Mariei stau în ../shared — dev server-ul trebuie să le poată citi
  server: { fs: { allow: ['..'] } },
})
