from __future__ import annotations
import re

# Mapa mínimo de equipos (extiéndelo si ves variantes)
_TEAM_ALIASES = {
    "red bull": "Red Bull Racing",
    "red bull racing": "Red Bull Racing",
    "rb": "Racing Bulls",
    "scuderia alphatauri": "Racing Bulls",
    "alphatauri": "Racing Bulls",
    "toro rosso": "Racing Bulls",
    "mclaren": "McLaren",
    "mercedes": "Mercedes",
    "ferrari": "Ferrari",
    "aston martin": "Aston Martin",
    "alpine": "Alpine",
    "renault": "Renault",
    "benetton": "Benetton",
    "williams": "Williams",
    "sauber": "Sauber",
    "stake": "Sauber",
    "haas": "Haas F1 Team",
    "alfa romeo": "Sauber",
    "racing point": "Aston Martin",
    "force india": "Aston Martin",
    "jordan": "Aston Martin",
}

def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def canonical_team(name: str) -> str:
    key = _clean(name).lower()
    return _TEAM_ALIASES.get(key, _clean(name))

def canonical_driver_broadcast(name: str) -> str:
    # Mantiene el nombre que viene de FastF1 (p.ej. "O PIASTRI") pero limpia espacios
    return _clean(name)

def canonical_driver_from_ergast(given: str, family: str, code: str | None = None) -> str:
    # Usa nombre completo "Nombre APELLIDO"
    g = _clean(given)
    f = _clean(family).upper()
    return f"{g} {f}".strip()
