"""🔍 Verificatorul terț: calculează pe datele băncii FĂRĂ să le vadă (ARCHITECTURE.md §6).

Primește doar bytes: contextul CKKS public (fără cheia secretă) și vectorii criptați.
Întoarce tot bytes: diferența criptată. Nu importă nimic din bancă și nu poate decripta.

    diff = 0,585·G + 0,415·N + 0,1·D + R − net_declarat
    (G brut, N sumă netaxabilă, D deducere personală, R corecția de rotunjire pe componente)
"""
import tenseal as ts

FORMULA = "0,585·G + 0,415·N + 0,1·D + R − net"


def compute_net_diff(package: dict[str, bytes]) -> bytes:
    ctx = ts.context_from(package["context"])
    if ctx.has_secret_key():
        raise ValueError("verificatorul nu are voie să primească cheia secretă")
    g, n, d, r, net = (ts.ckks_vector_from(ctx, package[k]) for k in ("gross", "untaxed", "deduction",
                                                                       "rounding", "declared_net"))
    return (g * 0.585 + n * 0.415 + d * 0.1 + r - net).serialize()
