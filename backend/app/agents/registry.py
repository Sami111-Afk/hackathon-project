"""Ce agent rulează pentru fiecare pas.

Cât timp agentul tău nu e gata, rulează varianta „de probă” (stub), care
redă rezultatul din dosarul Mariei. Când e gata, înlocuiești aici linia ta:

    from app.agents.paznic.agent import Paznic
    "paznic": Paznic(),
"""
import logging

from app.agents.compliance.agent import Compliance
from app.agents.detectiv.agent import Detectiv
from app.agents.functionar.agent import Functionar
from app.agents.paznic.agent import Paznic
from app.agents.paznic.ocr import ocr_available
from app.agents.stubs import StubAgent
from app.agents.verificator.agent import Verificator


def _paznic():
    # fără Tesseract `ron` pozele nu pot fi redactate → pe laptopurile fără el rămâne varianta de probă
    if ocr_available():
        return Paznic()
    logging.getLogger("orb.registry").warning("Tesseract `ron` lipsește: Paznic rulează în varianta de probă")
    return StubAgent("paznic", "Ascund datele personale", delay=1.5)


AGENTS = {
    "paznic": _paznic(),                                                        # Narcis
    "functionar": Functionar(),                                                 # Stefan
    "verificator": Verificator(),                                               # Stefan
    "detector": StubAgent("detector", "Caut urme de editare", delay=2.5),       # Narcis
    "detectiv": Detectiv(),                                                     # Erin
    "compliance": Compliance(),                                                 # Samuel
}
