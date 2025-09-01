from __future__ import annotations
from pathlib import Path
from typing import Dict, Tuple
import re, json, urllib.request
import pandas as pd
import yaml

# === Lineajes (ya existía) ===
def load_lineages(path: str = "config/lineage.yaml") -> Dict:
    p = Path(path)
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}

def apply_lineage_grouping(df: pd.DataFrame, team_col: str, agg_cols, sum_points: bool, lineage_map: Dict) -> pd.DataFrame:
    if not lineage_map or df.empty:
        return df
    rev = {}
    for root, nodes in lineage_map.items():
        for n in nodes:
            rev[n] = root
        rev[root] = root
    out = df.copy()
    out[team_col] = out[team_col].map(lambda x: rev.get(str(x), str(x)))
    if sum_points:
        agg = {c: ("sum" if c.lower().startswith("puntos") else "mean") for c in agg_cols}
    else:
        agg = {c: ("mean") for c in agg_cols}
    out = out.groupby(team_col, as_index=False).agg(agg)
    return out

# === NUEVO: normalización de nombres ===
def _load_naming_cfg(path: str = "config/naming.yaml") -> Tuple[Dict[str,str], Dict[str,str]]:
    p = Path(path)
    if not p.exists():
        return {}, {}
    cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    teams = {k.strip(): v.strip() for k, v in (cfg.get("teams") or {}).items()}
    drivers = {k.strip(): v.strip() for k, v in (cfg.get("drivers") or {}).items()}
    return teams, drivers

def _norm_lookup(name: str, mapping: Dict[str,str]) -> str:
    if not name:
        return name
    # Búsqueda case-insensitive
    for k, v in mapping.items():
        if k.lower() == str(name).lower():
            return v
    return name

def normalize_team(name: str) -> str:
    teams, _ = _load_naming_cfg()
    return _norm_lookup(name, teams)

def normalize_driver(name: str) -> str:
    _, drivers = _load_naming_cfg()
    return _norm_lookup(name, drivers)

def _looks_like_broadcast_initial(name: str) -> bool:
    # "M VERSTAPPEN", "C SAINZ", "L HAMILTON"...
    return bool(re.match(r"^[A-Z]\s+[A-ZÀ-ÿ'’\-]+$", str(name).strip()))

def _ergast_fullnames(season: int, rnd: int) -> Dict[str,str]:
    """Mapa: (APELLIDO en mayúsculas) -> 'Nombre Apellido' usando Ergast del mismo GP."""
    url = f"https://ergast.com/api/f1/{season}/{rnd}/results.json?limit=200"
    with urllib.request.urlopen(url, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    out = {}
    if not races:
        return out
    for r in races[0].get("Results", []):
        drv = r.get("Driver", {})
        given = (drv.get("givenName") or "").strip()
        family = (drv.get("familyName") or "").strip()
        if family:
            out[family.upper()] = f"{given} {family}".strip()
    return out

def normalize_base(df: pd.DataFrame, season: int, rnd: int) -> pd.DataFrame:
    """
    df columnas: Piloto, Equipo, Parrilla, Final
    - Expande 'M VERSTAPPEN' -> 'Max Verstappen' usando Ergast del mismo GP.
    - Aplica mapping de equipos/ pilotos de config/naming.yaml
    """
    if df.empty:
        return df
    base = df.copy()

    # 1) Expandir pilotos "Inicial APELLIDO" a "Nombre Apellido" si podemos
    try:
        need_expand = base["Piloto"].map(_looks_like_broadcast_initial).any()
    except Exception:
        need_expand = False
    if need_expand:
        try:
            fmap = _ergast_fullnames(season, rnd)  # {APELLIDO: Nombre Apellido}
        except Exception:
            fmap = {}
        def _expand(name: str) -> str:
            if not _looks_like_broadcast_initial(name):
                return name
            parts = name.strip().split()
            last = parts[-1].upper() if parts else ""
            return fmap.get(last, name.title())  # fallback: capitalizar
        base["Piloto"] = base["Piloto"].map(_expand)

    # 2) Normalizar por config
    teams_map, drivers_map = _load_naming_cfg()
    if teams_map:
        base["Equipo"] = base["Equipo"].map(lambda x: _norm_lookup(str(x), teams_map))
    if drivers_map:
        base["Piloto"] = base["Piloto"].map(lambda x: _norm_lookup(str(x), drivers_map))

    return base
