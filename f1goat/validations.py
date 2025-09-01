from __future__ import annotations
from typing import List, Tuple
import pandas as pd
from .storage import load_latest_gp, _connect

def _ok(b: bool) -> str: return "OK" if b else "FAIL"

def validate_latest_event() -> List[Tuple[str, str, str]]:
    out = []
    d, t, name, season, rnd = load_latest_gp()
    out.append(("Último evento", "existe", _ok(d is not None and t is not None and name is not None)))
    if d is None or t is None:
        return out
    out.append(("Último evento", f"{name} (season={season}, round={rnd})", "INFO"))
    # 1) filas pilotos > 0
    out.append(("Pilotos", "filas > 0", _ok(len(d) > 0)))
    # 2) columnas requeridas
    req_cols_d = ["Piloto","Equipo","Parrilla","Final","CSI","RR","QR","TD","PF","Puntos F1GOAT (GP)"]
    out.append(("Pilotos", "columnas requeridas", _ok(all(c in d.columns for c in req_cols_d))))
    # 3) puntos en [0,10]
    if "Puntos F1GOAT (GP)" in d.columns:
        m, M = float(d["Puntos F1GOAT (GP)"].min()), float(d["Puntos F1GOAT (GP)"].max())
        out.append(("Pilotos", "0 ≤ Puntos GP ≤ 10", _ok(m >= 0 - 1e-6 and M <= 10 + 1e-6)))
    # 4) nulos críticos (Piloto, Equipo no nulos)
    out.append(("Pilotos", "Piloto/Equipo no nulos", _ok(d["Piloto"].notna().all() and d["Equipo"].notna().all())))
    # 5) constructores: columnas clave + puntos en [0,10]
    req_cols_t = ["Equipo","Parrilla media","Final media","CSI medio","Ops","Rel","Dev","Puntos F1GOAT (GP)"]
    out.append(("Constructores", "columnas requeridas", _ok(all(c in t.columns for c in req_cols_t))))
    if "Puntos F1GOAT (GP)" in t.columns:
        m, M = float(t["Puntos F1GOAT (GP)"].min()), float(t["Puntos F1GOAT (GP)"].max())
        out.append(("Constructores", "0 ≤ Puntos GP ≤ 10", _ok(m >= 0 - 1e-6 and M <= 10 + 1e-6)))
    return out

def format_report(rows: List[Tuple[str,str,str]]) -> str:
    # Tabla simple alineada
    sec = ""
    for a, b, c in rows:
        sec += f"{a:15} | {b:45} | {c}\n"
    return sec

def quick_summary() -> str:
    with _connect() as con:
        ev = con.sql("SELECT COUNT(*) n FROM gp_events").df().iloc[0]["n"]
        dr = con.sql("SELECT COUNT(*) n FROM gp_driver_results").df().iloc[0]["n"]
        tm = con.sql("SELECT COUNT(*) n FROM gp_team_results").df().iloc[0]["n"]
        return f"gp_events={ev}, gp_driver_results={dr}, gp_team_results={tm}"
