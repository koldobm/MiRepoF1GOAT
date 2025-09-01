from typing import List, Dict, Tuple, Optional
import pandas as pd
from .compute import compute_gp_points_f1goat, compute_csi

DRIVERS: List[str] = [
    "Max Verstappen","Sergio Pérez","Lewis Hamilton","George Russell","Fernando Alonso","Lance Stroll",
    "Charles Leclerc","Carlos Sainz","Lando Norris","Oscar Piastri","Esteban Ocon","Pierre Gasly",
    "Valtteri Bottas","Zhou Guanyu","Yuki Tsunoda","Daniel Ricciardo","Kevin Magnussen","Nico Hulkenberg",
    "Alexander Albon","Logan Sargeant"
]
TEAM_OF: Dict[str, str] = {
    "Max Verstappen":"Red Bull Racing","Sergio Pérez":"Red Bull Racing",
    "Lewis Hamilton":"Mercedes","George Russell":"Mercedes",
    "Fernando Alonso":"Aston Martin","Lance Stroll":"Aston Martin",
    "Charles Leclerc":"Ferrari","Carlos Sainz":"Ferrari",
    "Lando Norris":"McLaren","Oscar Piastri":"McLaren",
    "Esteban Ocon":"Alpine","Pierre Gasly":"Alpine",
    "Valtteri Bottas":"Sauber","Zhou Guanyu":"Sauber",
    "Yuki Tsunoda":"RB","Daniel Ricciardo":"RB",
    "Kevin Magnussen":"Haas","Nico Hulkenberg":"Haas",
    "Alexander Albon":"Williams","Logan Sargeant":"Williams"
}
TEAM_STRENGTH = {
    "Red Bull Racing":1.18,"Mercedes":1.10,"Ferrari":1.08,"McLaren":1.06,
    "Aston Martin":1.02,"Alpine":0.98,"Sauber":0.94,"RB":0.96,"Haas":0.92,"Williams":0.90
}
TEAM_OPS = {k: round(7.5 + (v-1.0)*10, 2) for k,v in TEAM_STRENGTH.items()}
TEAM_REL = {k: round(7.0 + (v-1.0)*8,  2) for k,v in TEAM_STRENGTH.items()}
TEAM_DEV = {k: round(6.8 + (v-1.0)*12, 2) for k,v in TEAM_STRENGTH.items()}

def official_gp_name(season:int, rnd:int) -> str:
    return f"{season} — Gran Premio Simulado (R{rnd})"

def _components_for_pos(pos:int, rnd:int) -> Tuple[float,float,float,Optional[float],Optional[float]]:
    rr = max(0.0, 10.0 - 0.35*(pos-1))
    qr = max(0.0, 10.0 - 0.30*((pos+2)%20))
    td = max(0.0,  9.0 - 0.25*(pos-1))
    oq = 8.5 - 0.4*(pos-1) if pos <= 12 else None
    wa = 7.0 - 0.3*(pos-1) if (rnd % 5 == 0) else None
    return rr, qr, td, oq, wa

def simulate_gp(season:int, rnd:int):
    name = official_gp_name(season, rnd)
    order = list(range(len(DRIVERS)))
    shift = (rnd - 1) % len(DRIVERS)
    order = order[shift:] + order[:shift]
    rows = []
    for pos, idx in enumerate(order, start=1):
        d = DRIVERS[idx]; team = TEAM_OF[d]
        rr, qr, td, oq, wa = _components_for_pos(pos, rnd); pf = 0.0
        pts = compute_gp_points_f1goat(rr, qr, td, oq, wa, pf)
        csi = compute_csi(rr, qr, td, oq, wa, TEAM_STRENGTH.get(team, 1.0))
        rows.append({
            "Piloto": d, "Equipo": team, "Parrilla": pos, "Final": pos,
            "CSI": csi,
            "RR": round(rr,2), "QR": round(qr,2), "TD": round(td,2),
            "OQ": None if oq is None else round(oq,2),
            "WA": None if wa is None else round(wa,2),
            "PF": pf,
            "Puntos F1GOAT (GP)": pts
        })
    drivers = pd.DataFrame(rows)

    agg = drivers.groupby("Equipo", as_index=False).agg({
        "CSI":"mean","Parrilla":"mean","Final":"mean"
    }).rename(columns={"CSI":"CSI medio","Parrilla":"Parrilla media","Final":"Final media"})
    agg["Ops"] = agg["Equipo"].map(TEAM_OPS)
    agg["Rel"] = agg["Equipo"].map(TEAM_REL)
    agg["Dev"] = agg["Equipo"].map(TEAM_DEV)
    agg["Puntos F1GOAT (GP)"] = (0.6*agg["CSI medio"] + 0.2*agg["Ops"] + 0.1*agg["Rel"] + 0.1*agg["Dev"]).round(3)

    teams = agg[["Equipo","Parrilla media","Final media","CSI medio","Ops","Rel","Dev","Puntos F1GOAT (GP)"]]
    return drivers, teams, name

def simulate_season(season:int, rounds:int=8):
    import pandas as pd
    d_rounds = []; t_rounds = []
    for rnd in range(1, rounds+1):
        ddf, tdf, _ = simulate_gp(season, rnd)
        ddf = ddf.assign(Ronda=rnd)
        tdf = tdf.assign(Ronda=rnd)
        d_rounds.append(ddf); t_rounds.append(tdf)
    d_rounds = pd.concat(d_rounds, ignore_index=True)
    t_rounds = pd.concat(t_rounds, ignore_index=True)

    d_rounds["Acum"] = d_rounds.groupby("Piloto")["Puntos F1GOAT (GP)"].cumsum()
    t_rounds["Acum"] = t_rounds.groupby("Equipo")["Puntos F1GOAT (GP)"].cumsum()

    cap_max = 10.0 * rounds
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
        "Parrilla media":"mean","Final media":"mean","CSI medio":"mean","Ops":"mean","Rel":"mean","Dev":"mean",
        "Puntos F1GOAT (GP)":"sum","Acum":"max","Acum 0–100":"max"
    }).rename(columns={"Puntos F1GOAT (GP)":"Total GP"})

    for df in (d_final, t_final):
        for col in df.columns:
            if df[col].dtype.kind in "fc":
                df[col] = df[col].round(3)
    return d_rounds, t_rounds, d_final, t_final
