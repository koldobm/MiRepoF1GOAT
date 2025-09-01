from __future__ import annotations
from pathlib import Path
from typing import Tuple, Optional, List
import duckdb
import pandas as pd

DB_PATH = Path("data/f1goat.duckdb")

DDL = r"""
CREATE TABLE IF NOT EXISTS gp_events (
  event_key TEXT PRIMARY KEY,   -- "2025_22"
  season INTEGER NOT NULL,
  round INTEGER NOT NULL,
  official_name TEXT NOT NULL,
  event_date DATE
);

CREATE TABLE IF NOT EXISTS gp_driver_results (
  event_key TEXT NOT NULL,
  driver TEXT NOT NULL,
  team TEXT NOT NULL,
  grid INTEGER,
  finish INTEGER,
  csi DOUBLE,
  rr DOUBLE, qr DOUBLE, td DOUBLE, oq DOUBLE, wa DOUBLE, pf DOUBLE,
  points_gp DOUBLE,
  PRIMARY KEY (event_key, driver)
);

CREATE TABLE IF NOT EXISTS gp_team_results (
  event_key TEXT NOT NULL,
  team TEXT NOT NULL,
  parrilla_media DOUBLE,
  final_media DOUBLE,
  csi_medio DOUBLE,
  ops DOUBLE, rel DOUBLE, dev DOUBLE,
  points_gp DOUBLE,
  PRIMARY KEY (event_key, team)
);
"""

def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(DB_PATH.as_posix())
    con.sql(DDL)
    return con

# ---------- UPSERTS ----------

def upsert_event(season:int, rnd:int, official_name:str, event_date) -> str:
    key = f"{season}_{rnd:02d}"
    with _connect() as con:
        con.execute("INSERT OR REPLACE INTO gp_events VALUES (?, ?, ?, ?, ?)",
                    [key, season, rnd, official_name, event_date])
    return key

def upsert_driver_results(event_key:str, df: pd.DataFrame):
    with _connect() as con:
        con.execute("BEGIN")
        for _, r in df.iterrows():
            con.execute("""INSERT OR REPLACE INTO gp_driver_results
                (event_key, driver, team, grid, finish, csi, rr, qr, td, oq, wa, pf, points_gp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [event_key, r["Piloto"], r["Equipo"],
                 int(r["Parrilla"]) if pd.notna(r["Parrilla"]) else None,
                 int(r["Final"]) if pd.notna(r["Final"]) else None,
                 float(r["CSI"]) if pd.notna(r["CSI"]) else None,
                 *[ None if pd.isna(v) else float(v) for v in (r.get("RR"), r.get("QR"), r.get("TD"), r.get("OQ"), r.get("WA")) ],
                 float(r.get("PF", 0.0)) if pd.notna(r.get("PF", 0.0)) else 0.0,
                 float(r["Puntos F1GOAT (GP)"]) if pd.notna(r["Puntos F1GOAT (GP)"]) else None
                ])
        con.execute("COMMIT")

def upsert_team_results(event_key:str, df: pd.DataFrame):
    with _connect() as con:
        con.execute("BEGIN")
        for _, r in df.iterrows():
            con.execute("""INSERT OR REPLACE INTO gp_team_results
                (event_key, team, parrilla_media, final_media, csi_medio, ops, rel, dev, points_gp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [event_key, r["Equipo"],
                 *[ None if pd.isna(v) else float(v) for v in (
                    r.get("Parrilla media"), r.get("Final media"), r.get("CSI medio"),
                    r.get("Ops"), r.get("Rel"), r.get("Dev"), r.get("Puntos F1GOAT (GP)")
                 ) ]
                ])
        con.execute("COMMIT")

# ---------- ÚLTIMO GP (con resultados) ----------

def load_latest_gp() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[str], Optional[int], Optional[int]]:
    with _connect() as con:
        ev = con.sql("""
            SELECT e.*
            FROM gp_events e
            JOIN gp_driver_results d ON d.event_key = e.event_key
            WHERE e.round >= 1
            GROUP BY e.event_key, e.season, e.round, e.official_name, e.event_date
            ORDER BY e.event_date DESC, e.season DESC, e.round DESC
            LIMIT 1
        """).df()
        if ev.empty:
            return None, None, None, None, None
        key = ev.iloc[0]["event_key"]
        name = ev.iloc[0]["official_name"]
        season = int(ev.iloc[0]["season"]); rnd = int(ev.iloc[0]["round"])

        d = con.sql(
            "SELECT driver AS Piloto, team AS Equipo, grid AS Parrilla, finish AS Final, "
            "csi AS CSI, rr AS RR, qr AS QR, td AS TD, oq AS OQ, wa AS WA, pf AS PF, points_gp AS \"Puntos F1GOAT (GP)\" "
            "FROM gp_driver_results WHERE event_key = ? ORDER BY points_gp DESC, finish ASC",
            params=[key]
        ).df()

        t = con.sql(
            "SELECT team AS \"Equipo\", parrilla_media AS \"Parrilla media\", final_media AS \"Final media\", "
            "csi_medio AS \"CSI medio\", ops AS \"Ops\", rel AS \"Rel\", dev AS \"Dev\", "
            "points_gp AS \"Puntos F1GOAT (GP)\" "
            "FROM gp_team_results WHERE event_key = ? ORDER BY points_gp DESC",
            params=[key]
        ).df()

        return d, t, name, season, rnd

def load_gp(season:int, rnd:int) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[str]]:
    key = f"{season}_{rnd:02d}"
    with _connect() as con:
        ev = con.sql("SELECT official_name FROM gp_events WHERE event_key = ? AND round >= 1", params=[key]).df()
        if ev.empty:
            return None, None, None
        name = ev.iloc[0]["official_name"]

        d = con.sql(
            "SELECT driver AS Piloto, team AS Equipo, grid AS Parrilla, finish AS Final, "
            "csi AS CSI, rr AS RR, qr AS QR, td AS TD, oq AS OQ, wa AS WA, pf AS PF, points_gp AS \"Puntos F1GOAT (GP)\" "
            "FROM gp_driver_results WHERE event_key = ? ORDER BY points_gp DESC, finish ASC",
            params=[key]
        ).df()

        t = con.sql(
            "SELECT team AS \"Equipo\", parrilla_media AS \"Parrilla media\", final_media AS \"Final media\", "
            "csi_medio AS \"CSI medio\", ops AS \"Ops\", rel AS \"Rel\", dev AS \"Dev\", "
            "points_gp AS \"Puntos F1GOAT (GP)\" "
            "FROM gp_team_results WHERE event_key = ? ORDER BY points_gp DESC",
            params=[key]
        ).df()
        return d, t, name

# ---------- LISTAS PARA SELECTORES ----------

def list_seasons() -> List[int]:
    with _connect() as con:
        df = con.sql("SELECT DISTINCT season FROM gp_events WHERE round >= 1 ORDER BY season DESC").df()
        return [int(x) for x in df["season"].tolist()]

def list_rounds(season:int) -> List[int]:
    with _connect() as con:
        df = con.sql("SELECT DISTINCT round FROM gp_events WHERE season = ? AND round >= 1 ORDER BY round ASC",
                     params=[season]).df()
        return [int(x) for x in df["round"].tolist()]

def list_rounds_with_names(season:int) -> List[tuple[int,str]]:
    with _connect() as con:
        df = con.sql("SELECT round, official_name FROM gp_events WHERE season = ? AND round >= 1 ORDER BY round ASC",
                     params=[season]).df()
        return [(int(r["round"]), str(r["official_name"])) for _, r in df.iterrows()]

# ---------- TEMPORADA (agregados reales) ----------

def load_season(season:int) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    with _connect() as con:
        d_rounds = con.sql(
            "SELECT e.round AS Ronda, e.official_name AS GP, d.driver AS Piloto, d.team AS Equipo, "
            "d.grid AS Parrilla, d.finish AS Final, d.csi AS CSI, d.rr AS RR, d.qr AS QR, d.td AS TD, "
            "d.oq AS OQ, d.wa AS WA, d.pf AS PF, d.points_gp AS \"Puntos F1GOAT (GP)\" "
            "FROM gp_driver_results d JOIN gp_events e ON d.event_key = e.event_key "
            "WHERE e.season = ? AND e.round >= 1 "
            "ORDER BY Ronda ASC, \"Puntos F1GOAT (GP)\" DESC, Final ASC",
            params=[season]
        ).df()

        t_rounds = con.sql(
            "SELECT e.round AS Ronda, e.official_name AS GP, t.team AS \"Equipo\", "
            "t.parrilla_media AS \"Parrilla media\", t.final_media AS \"Final media\", t.csi_medio AS \"CSI medio\", "
            "t.ops AS \"Ops\", t.rel AS \"Rel\", t.dev AS \"Dev\", t.points_gp AS \"Puntos F1GOAT (GP)\" "
            "FROM gp_team_results t JOIN gp_events e ON t.event_key = e.event_key "
            "WHERE e.season = ? AND e.round >= 1 "
            "ORDER BY Ronda ASC, \"Puntos F1GOAT (GP)\" DESC",
            params=[season]
        ).df()

    if d_rounds.empty or t_rounds.empty:
        return (pd.DataFrame(columns=["Ronda","GP","Piloto","Equipo","Parrilla","Final","CSI","RR","QR","TD","OQ","WA","PF","Puntos F1GOAT (GP)"]),
                pd.DataFrame(columns=["Ronda","GP","Equipo","Parrilla media","Final media","CSI medio","Ops","Rel","Dev","Puntos F1GOAT (GP)"]),
                pd.DataFrame(), pd.DataFrame())

    rounds = int(max(d_rounds["Ronda"]))
    cap_max = 10.0 * rounds
    d_rounds = d_rounds.sort_values(["Piloto","Ronda"])
    t_rounds = t_rounds.sort_values(["Equipo","Ronda"])
    d_rounds["Acum"] = d_rounds.groupby("Piloto")["Puntos F1GOAT (GP)"].cumsum()
    t_rounds["Acum"] = t_rounds.groupby("Equipo")["Puntos F1GOAT (GP)"].cumsum()
    d_rounds["Acum 0–100"] = (d_rounds["Acum"] / cap_max) * 100.0
    t_rounds["Acum 0–100"] = (t_rounds["Acum"] / cap_max) * 100.0

    d_final = d_rounds.groupby(["Piloto","Equipo"], as_index=False).agg({
        "Parrilla":"mean","Final":"mean","CSI":"mean","RR":"mean","QR":"mean","TD":"mean",
        "OQ":"mean","WA":"mean","PF":"mean","Puntos F1GOAT (GP)":"sum","Acum":"max","Acum 0–100":"max"
    }).rename(columns={
        "Parrilla":"Parrilla media","Final":"Final media","CSI":"CSI medio",
        "RR":"RR medio","QR":"QR medio","TD":"TD medio",
        "OQ":"OQ medio","WA":"WA medio","PF":"PF medio","Puntos F1GOAT (GP)":"Total GP"
    })

    t_final = t_rounds.groupby("Equipo", as_index=False).agg({
        "Parrilla media":"mean","Final media":"mean","CSI medio":"mean",
        "Ops":"mean","Rel":"mean","Dev":"mean",
        "Puntos F1GOAT (GP)":"sum","Acum":"max","Acum 0–100":"max"
    }).rename(columns={"Puntos F1GOAT (GP)":"Total GP"})

    for df in (d_final, t_final):
        for col in df.columns:
            if df[col].dtype.kind in "fc":
                df[col] = df[col].round(3)

    return d_rounds, t_rounds, d_final, t_final

# ---------- HISTÓRICO Y MEJORES TEMPORADAS (para páginas 03 y 04) ----------

def load_all_driver_results() -> pd.DataFrame:
    with _connect() as con:
        return con.sql(
            "SELECT e.season AS Temporada, e.round AS Ronda, e.official_name AS GP, "
            "d.driver AS Piloto, d.team AS Equipo, d.grid AS Parrilla, d.finish AS Final, "
            "d.csi AS CSI, d.rr AS RR, d.qr AS QR, d.td AS TD, d.oq AS OQ, d.wa AS WA, d.pf AS PF, "
            "d.points_gp AS \"Puntos F1GOAT (GP)\" "
            "FROM gp_driver_results d JOIN gp_events e ON d.event_key = e.event_key "
            "WHERE e.round >= 1"
        ).df()

def load_all_team_results() -> pd.DataFrame:
    with _connect() as con:
        return con.sql(
            "SELECT e.season AS Temporada, e.round AS Ronda, e.official_name AS GP, "
            "t.team AS Equipo, t.parrilla_media AS \"Parrilla media\", t.final_media AS \"Final media\", "
            "t.csi_medio AS \"CSI medio\", t.ops AS \"Ops\", t.rel AS \"Rel\", t.dev AS \"Dev\", "
            "t.points_gp AS \"Puntos F1GOAT (GP)\" "
            "FROM gp_team_results t JOIN gp_events e ON t.event_key = e.event_key "
            "WHERE e.round >= 1"
        ).df()

# ---------- AVISO: calendario vs con resultados ----------

def get_latest_calendar_event() -> Optional[dict]:
    with _connect() as con:
        df = con.sql("SELECT * FROM gp_events WHERE round >= 1 ORDER BY event_date DESC, season DESC, round DESC LIMIT 1").df()
        if df.empty: return None
        r = df.iloc[0]
        return {"event_key": r["event_key"], "season": int(r["season"]), "round": int(r["round"]), "official_name": r["official_name"], "date": r["event_date"]}

def get_latest_results_event() -> Optional[dict]:
    with _connect() as con:
        df = con.sql("""
            SELECT e.*
            FROM gp_events e
            JOIN gp_driver_results d ON d.event_key = e.event_key
            WHERE e.round >= 1
            GROUP BY e.event_key, e.season, e.round, e.official_name, e.event_date
            ORDER BY e.event_date DESC, e.season DESC, e.round DESC
            LIMIT 1
        """).df()
        if df.empty: return None
        r = df.iloc[0]
        return {"event_key": r["event_key"], "season": int(r["season"]), "round": int(r["round"]), "official_name": r["official_name"], "date": r["event_date"]}

# ---------- DIAGNÓSTICO ----------

def _debug_summary() -> str:
    with _connect() as con:
        ev = con.sql("SELECT COUNT(*) AS n FROM gp_events").df().iloc[0]["n"]
        dr = con.sql("SELECT COUNT(*) AS n FROM gp_driver_results").df().iloc[0]["n"]
        tm = con.sql("SELECT COUNT(*) AS n FROM gp_team_results").df().iloc[0]["n"]
        latest_cal = con.sql("""
            SELECT event_key, season, round, official_name, event_date
            FROM gp_events
            ORDER BY event_date DESC, season DESC, round DESC
            LIMIT 1
        """).df()
        latest_res = con.sql("""
            SELECT e.event_key, e.season, e.round, e.official_name, e.event_date
            FROM gp_events e
            JOIN gp_driver_results d ON d.event_key = e.event_key
            WHERE e.round >= 1
            GROUP BY e.event_key, e.season, e.round, e.official_name, e.event_date
            ORDER BY e.event_date DESC, e.season DESC, e.round DESC
            LIMIT 1
        """).df()
        hdr = f"Eventos: {ev} | Filas pilotos: {dr} | Filas constructores: {tm}\n"
        s_cal = "(vacío)" if latest_cal.empty else f"{latest_cal.iloc[0]['official_name']} (key={latest_cal.iloc[0]['event_key']}, season={int(latest_cal.iloc[0]['season'])}, round={int(latest_cal.iloc[0]['round'])}, date={latest_cal.iloc[0]['event_date']})"
        s_res = "(sin resultados)" if latest_res.empty else f"{latest_res.iloc[0]['official_name']} (key={latest_res.iloc[0]['event_key']}, season={int(latest_res.iloc[0]['season'])}, round={int(latest_res.iloc[0]['round'])}, date={latest_res.iloc[0]['event_date']})"
        return hdr + "Último calendario: " + s_cal + "\nÚltimo con resultados: " + s_res + "\n"
