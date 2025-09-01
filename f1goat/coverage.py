from __future__ import annotations
from .storage import _connect

def coverage_report() -> str:
    with _connect() as con:
        seasons = con.sql("SELECT DISTINCT season FROM gp_events WHERE round>=1 ORDER BY season ASC").df()["season"].tolist()
        lines = []
        for y in seasons:
            ev = con.sql("SELECT round, official_name FROM gp_events WHERE season=? AND round>=1 ORDER BY round", params=[y]).df()
            have = con.sql("""
                SELECT DISTINCT e.round
                FROM gp_events e JOIN gp_driver_results d ON e.event_key=d.event_key
                WHERE e.season=? AND e.round>=1
                ORDER BY e.round
            """, params=[y]).df()["round"].tolist()
            all_rounds = ev["round"].tolist()
            missing = [r for r in all_rounds if r not in have]
            lines.append(f"{y}: total={len(all_rounds)}, con_resultados={len(have)}, faltan={len(missing)}")
            if missing:
                for r in missing:
                    name = ev.loc[ev["round"]==r, "official_name"].iloc[0]
                    lines.append(f"  - R{int(r):02d} {name}")
        return "\n".join(lines) if lines else "No hay eventos registrados."
