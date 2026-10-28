"""🏦 Banca: verificarea netului pe date criptate (CKKS, TenSEAL). Vezi ARCHITECTURE.md §6.

Model de amenințare (spus onest): banca are deja datele în clar; HE permite ca un verificator
TERȚ să ruleze calculul fără să le vadă. CKKS dă confidențialitate, nu integritate: un
verificator rău-intenționat poate întoarce orice. Rezultatul decriptat NU pleacă niciodată
înapoi la verificator (decriptările CKKS partajate pot scurge cheia — Li–Micciancio).

Fluxul, cu serializare reală între cele două părți:
  banca:       G, N, D, R (calculate în clar, din tax.py) + netul declarat → vectori criptați
  verificator: he_verifier.compute_net_diff(bytes) → diferența criptată (bytes)
  banca:       decriptează → |diff| ≤ 2 lei pentru măcar o variantă de persoane în întreținere

R = netul rotunjit pe componente − forma liniară, deci rezultatul e identic cu tax.check_net.
CPU-intensiv → se apelează cu asyncio.to_thread.
"""
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from app.agents.verificator.tax import NET_TOLERANCE_RON, compute_payslip, expected_net

try:
    import tenseal as ts

    from app.agents.verificator import he_verifier
except ImportError:  # TenSEAL e în requirements-ml.txt; fără el Verificatorul calculează în clar
    ts = None
    he_verifier = None

POLY_MODULUS_DEGREE = 8192
COEFF_MOD_BIT_SIZES = [60, 40, 40, 60]
GLOBAL_SCALE = 2**40
MAX_DEPENDENTS = 4
# CKKS e aproximativ (eroare ~1e-3 lei la acești parametri): marja e sub un ban, ca o diferență
# de exact 2,00 lei să fie tratată ca în calculul în clar (acceptată), iar 2,01 lei nu
CKKS_EPSILON_RON = 0.005


def available() -> bool:
    return ts is not None


@dataclass(frozen=True)
class NetItem:
    doc_id: str
    gross: float
    declared_net: float
    period: str | None = None
    dependents: int | None = None  # None = nu scrie pe fluturaș → acceptăm 0–4, ca în check_net


@dataclass(frozen=True)
class NetCheck:
    doc_id: str
    ok: bool
    computed_net: float  # netul pentru prima variantă (0 persoane / cele declarate), pentru mesaj
    declared_net: float


@dataclass
class HEReport:
    checks: list[NetCheck]
    slots: int
    context_bytes: int
    ciphertext_bytes: int
    ciphertext_sample: str
    ms: int
    formula: str = field(default="")

    def artifacts(self) -> dict[str, str]:
        """Pentru UI (ARCHITECTURE §6): mărimi, latență, câțiva bytes din ciphertext — ilustrație, nu dovadă."""
        return {
            "he_scheme": f"CKKS, N={POLY_MODULUS_DEGREE}, scală 2^40",
            "he_formula": self.formula,
            "he_slots": str(self.slots),
            "he_context_kb": str(round(self.context_bytes / 1024)),
            "he_ciphertext_kb": str(round(self.ciphertext_bytes / 1024)),
            "he_ciphertext_sample": self.ciphertext_sample,
            "he_ms": str(self.ms),
        }


class Bank:
    """Ține cheia secretă. Contextul se generează o dată pe proces (~150 ms)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._ctx = None

    def _context(self):
        with self._lock:
            if self._ctx is None:
                ctx = ts.context(ts.SCHEME_TYPE.CKKS, poly_modulus_degree=POLY_MODULUS_DEGREE,
                                 coeff_mod_bit_sizes=COEFF_MOD_BIT_SIZES)
                ctx.global_scale = GLOBAL_SCALE  # fără galois keys: nu facem rotații
                self._ctx = ctx
            return self._ctx

    def verify_nets(self, items: list[NetItem],
                    verifier: Callable[[dict[str, bytes]], bytes] | None = None) -> HEReport:
        verifier = verifier or he_verifier.compute_net_diff
        t0 = time.perf_counter()
        ctx = self._context()

        owners, cols = [], {"gross": [], "untaxed": [], "deduction": [], "rounding": [], "declared_net": []}
        for i, item in enumerate(items):
            options = range(MAX_DEPENDENTS + 1) if item.dependents is None else [item.dependents]
            for dependents in options:
                t = compute_payslip(item.gross, dependents, None, item.period)
                owners.append(i)
                cols["gross"].append(item.gross)
                cols["untaxed"].append(t.untaxed)
                cols["deduction"].append(t.deduction)
                cols["rounding"].append(t.net - expected_net(item.gross, t.deduction, t.untaxed))
                cols["declared_net"].append(item.declared_net)

        package = {"context": ctx.serialize(save_secret_key=False)}
        package |= {k: ts.ckks_vector(ctx, v).serialize() for k, v in cols.items()}
        diff_bytes = verifier(package)  # doar bytes trec granița
        diffs = ts.ckks_vector_from(ctx, diff_bytes).decrypt()

        checks = []
        for i, item in enumerate(items):
            mine = [d for owner, d in zip(owners, diffs, strict=True) if owner == i]
            checks.append(NetCheck(item.doc_id, ok=any(abs(d) <= NET_TOLERANCE_RON + CKKS_EPSILON_RON for d in mine),
                                   computed_net=round(item.declared_net + mine[0], 2),
                                   declared_net=item.declared_net))
        sample = package["gross"]
        return HEReport(checks=checks, slots=len(owners), context_bytes=len(package["context"]),
                        ciphertext_bytes=sum(len(package[k]) for k in cols), ciphertext_sample=sample[64:80].hex(),
                        ms=int((time.perf_counter() - t0) * 1000),
                        formula=he_verifier.FORMULA if he_verifier else "")


bank = Bank()
