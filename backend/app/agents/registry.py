"""Ce agent rulează pentru fiecare pas.

Cât timp agentul tău nu e gata, rulează varianta „de probă” (stub), care
redă rezultatul din dosarul Mariei. Când e gata, înlocuiești aici linia ta:

    from app.agents.paznic.agent import Paznic
    "paznic": Paznic(),
"""
from app.agents.compliance.agent import Compliance
from app.agents.functionar.agent import Functionar
from app.agents.stubs import StubAgent

AGENTS = {
    "paznic": StubAgent("paznic", "Ascund datele personale", delay=1.5),        # Narcis
    "functionar": Functionar(),                                                 # Stefan
    "verificator": StubAgent("verificator", "Refac calculele", delay=1.8),      # Stefan
    "detector": StubAgent("detector", "Caut urme de editare", delay=2.5),       # Narcis
    "detectiv": StubAgent("detectiv", "Compar cu alte dosare", delay=0.5),      # Erin
    "compliance": Compliance(),                                                 # Samuel
}
