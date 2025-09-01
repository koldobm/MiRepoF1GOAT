from __future__ import annotations
from typing import Dict, List, Tuple
import pandas as pd
from .storage import _connect, list_seasons, load_season
from .eb import eb_adjust_means

def _compress_years(years: List[int]) -> str:
    years = sorted(set(int(y) for y in years))
    if not years: return ""
    ranges = []
    start = prev = years[0]
    for y in years[1:]:
        if y == prev + 1:
            prev = y
            continue
        ranges.append((start, prev))
        start = prev = y
    ranges.append((start, prev))
    parts = [f"{a}" if a==b else f"{a}-{b}" for (a,b) in ranges]
    return ", ".join(parts)

def _equipos_y_anios(df: pd.DataFrame) -> pd.DataFrame:
    # df con columnas: Piloto, Equipo, Season
    out = (df.groupby(['Piloto','Equipo'])['Season']
             .apply(lambda s: _compress_years(list(s)))
             .reset_index())
    out['pair'] = out.apply(lambda r: f"{r['Equipo']} ({r['Season']})" if r['Season'] else r['Equipo'], axis=1)
    cat = (out.groupby('Piloto')['pair'].apply(lambda s: "; ".join([p for p in s if p])).reset_index()
           .rename(columns={'pair':'Equipos y años'}))
    return cat

def historical_pilots_table() -> pd.DataFrame:
    """
    Construye tabla histórica (toda la DB) con:
      Piloto | Equipos y años | GPs | Parrilla media | Final media | CSI medio | RR medio | QR medio | TD medio | OQ medio | WA medio | Total acumulado | Media por GP (AJUSTADA EB)
    """
    with _connect() as con:
        pts = con.sql("""
            SELECT e.season AS Season, d.driver AS Piloto, d.team AS Equipo,
                   d.grid AS Parrilla, d.finish AS Final, d.csi AS CSI, d.rr AS RR, d.qr AS QR, d.td AS TD,
                   d.oq AS OQ, d.wa AS WA, d.pf AS PF, d.points_gp AS Puntos
            FROM gp_driver_results d
            JOIN gp_events e ON d.event_key = e.event_key
            WHERE e.round >= 1
        """).df()
    if pts.empty:
        return pd.DataFrame(columns=[
            "Piloto","Equipos y años","GPs","Parrilla media","Final media","CSI medio",
            "RR medio","QR medio","TD medio","OQ medio","WA medio","Total acumulado","Media por GP (AJUSTADA EB)"
        ])

    # EB (por piloto con Puntos por GP)
    eb = eb_adjust_means(pts.rename(columns={"Puntos":"P"}), group_col="Piloto", value_col="P")
    eb = eb.rename(columns={"n":"GPs","mean":"Media por GP","eb_mean":"Media por GP (AJUSTADA EB)"})[["Piloto","GPs","Media por GP (AJUSTADA EB)"]]

    # Agregados de columnas
    agg = (pts.groupby("Piloto", as_index=False)
              .agg({"Parrilla":"mean","Final":"mean","CSI":"mean","RR":"mean","QR":"mean","TD":"mean",
                    "OQ":"mean","WA":"mean","Puntos":"sum"}))
    agg = agg.rename(columns={"Parrilla":"Parrilla media","Final":"Final media","CSI":"CSI medio","RR":"RR medio","QR":"QR medio",
                              "TD":"TD medio","OQ":"OQ medio","WA":"WA medio","Puntos":"Total acumulado"})

    # Equipos y años
    equipos = _equipos_y_anios(pts[["Piloto","Equipo","Season"]])

    out = (agg.merge(eb, on="Piloto", how="left")
              .merge(equipos, on="Piloto", how="left"))

    # Redondeo amable
    for c in ["Parrilla media","Final media","CSI medio","RR medio","QR medio","TD medio","OQ medio","WA medio",
              "Total acumulado","Media por GP (AJUSTADA EB)"]:
        if c in out.columns:
            out[c] = out[c].astype(float).round(3)

    cols = ["Piloto","Equipos y años","GPs","Parrilla media","Final media","CSI medio",
            "RR medio","QR medio","TD medio","OQ medio","WA medio","Total acumulado","Media por GP (AJUSTADA EB)"]
    out = out[cols].sort_values(["Media por GP (AJUSTADA EB)","GPs"], ascending=[False, False])
    out.index = range(1, len(out)+1)
    out.index.name = "Pos"
    return out

def best_seasons_pilots() -> pd.DataFrame:
    """
    Tabla por piloto (agregado sobre temporadas) con:
      Piloto | Equipos (años) | GPs media | Temps. disputadas | 1º (años) | 2º (años) | 3º (años) | Media por temporada
    Ranking por 'Media por temporada' (SeasonCap 0–100).
    """
    seasons = list_seasons()
    if not seasons:
        return pd.DataFrame(columns=["Piloto","Equipos (años)","GPs media","Temps. disputadas","1º (años)","2º (años)","3º (años)","Media por temporada"])

    rows = []
    per_season_rank = []
    for y in sorted(seasons):
        d_rounds, t_rounds, d_final, _ = load_season(y)
        if d_final is None or d_final.empty: 
            continue
        # ranking de temporada (pilotos)
        dtmp = d_final[["Piloto","Acum 0–100"]].sort_values("Acum 0–100", ascending=False).reset_index(drop=True)
        dtmp["rank"] = dtmp.index + 1
        for _, r in dtmp.iterrows():
            per_season_rank.append({"Season": y, "Piloto": r["Piloto"], "rank": int(r["rank"])})
        # filas para medias
        d_final2 = d_final.copy()
        d_final2["Season"] = y
        # nº GPs disputados por piloto en la temporada = tamaño en d_rounds
        ngps = d_rounds.groupby("Piloto")["Ronda"].nunique().reset_index().rename(columns={"Ronda":"GPs temp."})
        d_final2 = d_final2.merge(ngps, on="Piloto", how="left")
        for _, r in d_final2.iterrows():
            rows.append({"Piloto": r["Piloto"], "Season": y, "Acum100": r["Acum 0–100"], "GPs": int(r.get("GPs temp.", 0))})
    if not rows:
        return pd.DataFrame(columns=["Piloto","Equipos (años)","GPs media","Temps. disputadas","1º (años)","2º (años)","3º (años)","Media por temporada"])

    df = pd.DataFrame(rows)
    rnk = pd.DataFrame(per_season_rank)

    # Agregados por piloto
    base = (df.groupby("Piloto", as_index=False)
              .agg(GPs_media=("GPs","mean"),
                   Temps=("Season","nunique"),
                   MediaTemp=("Acum100","mean")))
    base["GPs_media"] = base["GPs_media"].round(2)
    base["Media por temporada"] = base["MediaTemp"].round(3)
    base["Temps. disputadas"] = base["Temps"].astype(int)
    base = base.drop(columns=["MediaTemp","Temps"])

    # 1º/2º/3º (años)
    pos = (rnk.pivot_table(index=["Piloto","Season"], columns="rank", values="rank", aggfunc="size", fill_value=0)
             .reset_index().rename_axis(None, axis=1))
    pos = pos.rename(columns={1:"is1",2:"is2",3:"is3"})
    pos["is1"] = pos.get("is1", 0); pos["is2"] = pos.get("is2", 0); pos["is3"] = pos.get("is3", 0)
    for col in ["is1","is2","is3"]:
        pos[col] = pos[col].astype(int)
    p1 = pos[pos["is1"]==1].groupby("Piloto")["Season"].apply(lambda s: ", ".join(str(int(x)) for x in sorted(s))).reset_index(name="1º (años)")
    p2 = pos[pos["is2"]==1].groupby("Piloto")["Season"].apply(lambda s: ", ".join(str(int(x)) for x in sorted(s))).reset_index(name="2º (años)")
    p3 = pos[pos["is3"]==1].groupby("Piloto")["Season"].apply(lambda s: ", ".join(str(int(x)) for x in sorted(s))).reset_index(name="3º (años)")
    counts = (pos.groupby("Piloto")[["is1","is2","is3"]].sum().reset_index()
                .merge(p1, on="Piloto", how="left")
                .merge(p2, on="Piloto", how="left")
                .merge(p3, on="Piloto", how="left"))
    for col, name in [("is1","1º (años)"),("is2","2º (años)"),("is3","3º (años)")]:
        counts[name] = counts[col].astype(int).astype(str) + " (" + counts[name].fillna("").astype(str) + ")"
    counts = counts[["Piloto","1º (años)","2º (años)","3º (años)"]]

    # Equipos (años) a nivel carrera
    with _connect() as con:
        pty = con.sql("""
            SELECT e.season AS Season, d.driver AS Piloto, d.team AS Equipo
            FROM gp_driver_results d JOIN gp_events e ON d.event_key = e.event_key
            WHERE e.round >= 1
        """).df()
    eq = (pty.groupby(['Piloto','Equipo'])['Season']
            .apply(lambda s: _compress_years(list(s))).reset_index())
    eq['pair'] = eq.apply(lambda r: f"{r['Equipo']} ({r['Season']})" if r['Season'] else r['Equipo'], axis=1)
    eq2 = (eq.groupby('Piloto')['pair'].apply(lambda s: "; ".join([p for p in s if p])).reset_index()
             .rename(columns={'pair':'Equipos (años)'}))

    out = (base.merge(counts, on="Piloto", how="left")
               .merge(eq2, on="Piloto", how="left"))
    out = out.rename(columns={"GPs_media":"GPs media"})
    cols = ["Piloto","Equipos (años)","GPs media","Temps. disputadas","1º (años)","2º (años)","3º (años)","Media por temporada"]
    out = out[cols].sort_values(["Media por temporada","Temps. disputadas"], ascending=[False, False])
    out.index = range(1, len(out)+1); out.index.name = "Pos"
    return out

def best_seasons_teams() -> pd.DataFrame:
    """
    Tabla por equipo (agregado sobre temporadas) con:
      Equipo | GPs media | Temps. disputadas | 1º (años) | 2º (años) | 3º (años) | Media por temporada
    """
    seasons = list_seasons()
    if not seasons:
        return pd.DataFrame(columns=["Equipo","GPs media","Temps. disputadas","1º (años)","2º (años)","3º (años)","Media por temporada"])

    rows = []
    per_season_rank = []
    for y in sorted(seasons):
        _, t_rounds, _, t_final = load_season(y)
        if t_final is None or t_final.empty:
            continue
        ttmp = t_final[["Equipo","Acum 0–100"]].sort_values("Acum 0–100", ascending=False).reset_index(drop=True)
        ttmp["rank"] = ttmp.index + 1
        for _, r in ttmp.iterrows():
            per_season_rank.append({"Season": y, "Equipo": r["Equipo"], "rank": int(r["rank"])})
        # nº GPs participados por equipo = nº rondas de esa temporada en t_rounds
        ngps = t_rounds.groupby("Equipo")["Ronda"].nunique().reset_index().rename(columns={"Ronda":"GPs temp."})
        tf2 = t_final.copy()
        tf2["Season"] = y
        tf2 = tf2.merge(ngps, on="Equipo", how="left")
        for _, r in tf2.iterrows():
            rows.append({"Equipo": r["Equipo"], "Season": y, "Acum100": r["Acum 0–100"], "GPs": int(r.get("GPs temp.", 0))})
    if not rows:
        return pd.DataFrame(columns=["Equipo","GPs media","Temps. disputadas","1º (años)","2º (años)","3º (años)","Media por temporada"])

    df = pd.DataFrame(rows)
    rnk = pd.DataFrame(per_season_rank)

    base = (df.groupby("Equipo", as_index=False)
              .agg(GPs_media=("GPs","mean"),
                   Temps=("Season","nunique"),
                   MediaTemp=("Acum100","mean")))
    base["GPs media"] = base["GPs_media"].round(2)
    base["Media por temporada"] = base["MediaTemp"].round(3)
    base["Temps. disputadas"] = base["Temps"].astype(int)
    base = base.drop(columns=["GPs_media","MediaTemp","Temps"])

    pos = (rnk.pivot_table(index=["Equipo","Season"], columns="rank", values="rank", aggfunc="size", fill_value=0)
             .reset_index().rename_axis(None, axis=1))
    pos = pos.rename(columns={1:"is1",2:"is2",3:"is3"})
    for col in ["is1","is2","is3"]:
        if col not in pos.columns: pos[col] = 0
        pos[col] = pos[col].astype(int)
    p1 = pos[pos["is1"]==1].groupby("Equipo")["Season"].apply(lambda s: ", ".join(str(int(x)) for x in sorted(s))).reset_index(name="1º (años)")
    p2 = pos[pos["is2"]==1].groupby("Equipo")["Season"].apply(lambda s: ", ".join(str(int(x)) for x in sorted(s))).reset_index(name="2º (años)")
    p3 = pos[pos["is3"]==1].groupby("Equipo")["Season"].apply(lambda s: ", ".join(str(int(x)) for x in sorted(s))).reset_index(name="3º (años)")
    counts = (pos.groupby("Equipo")[["is1","is2","is3"]].sum().reset_index()
                .merge(p1, on="Equipo", how="left")
                .merge(p2, on="Equipo", how="left")
                .merge(p3, on="Equipo", how="left"))
    for col, name in [("is1","1º (años)"),("is2","2º (años)"),("is3","3º (años)")]:
        counts[name] = counts[col].astype(int).astype(str) + " (" + counts[name].fillna("").astype(str) + ")"
    counts = counts[["Equipo","1º (años)","2º (años)","3º (años)"]]

    out = base.merge(counts, on="Equipo", how="left")
    cols = ["Equipo","GPs media","Temps. disputadas","1º (años)","2º (años)","3º (años)","Media por temporada"]
    out = out[cols].sort_values(["Media por temporada","Temps. disputadas"], ascending=[False, False])
    out.index = range(1, len(out)+1); out.index.name = "Pos"
    return out
