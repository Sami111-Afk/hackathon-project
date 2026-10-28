// Estompare scurtă între paginile băncii (View Transitions API). React Router o face singur doar cu
// createBrowserRouter; noi folosim <BrowserRouter>, așa că o pornim de mână la click în meniu.
// Nimic la prima încărcare a paginii, deci Lighthouse nu o vede.

let finish: (() => void) | null = null

/** Navighează cu estompare, dacă browserul o are și utilizatorul nu a cerut mai puțină mișcare. */
export function navigateWithFade(go: () => void) {
  if (!document.startViewTransition || matchMedia('(prefers-reduced-motion: reduce)').matches) return go()
  document.startViewTransition(() => new Promise<void>((resolve) => {
    finish = resolve
    go()
    setTimeout(resolve, 400) // plasă de siguranță: ecranul nu rămâne niciodată „înghețat”
  }))
}

/** Pagina nouă s-a desenat (apelat din AppNav): animația poate porni. */
export function pageDrawn() {
  finish?.()
  finish = null
}
