import os, sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
from f1goat.ui import render_legend
from f1goat.naming import load_lineages, apply_lineage_grouping
from f1goat.simdata import simulate_gp
from f1goat.storage import list_seasons, list_rounds_with_names, load_gp
from f1goat.compute import auto_table_height

st.set_page_config(page_title="F1GOAT — Gran Premio", page_icon="app/assets/f1goat.png", layout="wide")
st.title("🏁 Gran Premio")
render_legend(["gp_drivers","gp_teams"])

# Sidebar: toggles
if "group_lineage" not in st.session_state:
    st.session_state["group_lineage"] = False
st.sidebar.header("⚙️ Opciones")
st.session_state["group_lineage"] = st.sidebar.checkbox("Agrupar linajes de equipo", value=st.session_state["group_lineage"])
real_only = st.sidebar.checkbox("Solo datos reales (sin simulación)", value=False)

db_seasons = list_seasons()
if db_seasons:
    season = st.selectbox("Temporada", db_seasons, index=0)
    opts = list_rounds_with_names(season)  # [(rnd, "YYYY — Nombre oficial"), ...] ordenados por ronda ASC
    if not opts:
        st.warning("No hay eventos registrados en la DB para esta temporada.")
        st.stop()
    def _fmt(x):  # x = (rnd, name)
        rnd, nm = x
        return f"R{rnd:02d} — {nm}"
    choice = st.selectbox("Gran Premio", opts, index=len(opts)-1, format_func=_fmt)
    rnd = choice[0]
else:
    season = st.selectbox("Temporada", list(range(2025, 1949, -1)), index=0)
    rnd = st.selectbox("GP (ronda)", list(range(1, 23)), index=0)

drivers = teams = None
gp_name = None

d_real, t_real, name_real = load_gp(season, rnd)
if name_real:
    gp_name = name_real
if d_real is not None and not d_real.empty:
    drivers, teams = d_real, t_real

if drivers is None or teams is None:
    if real_only:
        st.error("Modo 'solo datos reales' activo y no hay resultados en la base para este GP.")
        st.stop()
    drivers, teams, gp_name = simulate_gp(season, rnd)

st.markdown(f"### {gp_name}")

# Pilotos
dcols = ["Piloto","Equipo","Parrilla","Final","CSI","RR","QR","TD","OQ","WA","PF","Puntos F1GOAT (GP)"]
dview = drivers[dcols].sort_values("Puntos F1GOAT (GP)", ascending=False).copy()
dview.index = pd.RangeIndex(1, len(dview)+1, name="Pos")
dview["Piloto"] = dview["Piloto"].astype(str).str.title().str.replace(r"^([A-Z])\\s+", r"\\1. ", regex=True)
st.subheader("Pilotos — GP (F1GOAT)")
st.dataframe(dview, use_container_width=True, height=auto_table_height(len(dview)))

# Constructores
mapping = load_lineages()
tview = teams.copy()
if st.session_state.get("group_lineage", False):
    tview = apply_lineage_grouping(tview, "Equipo",
        ["Parrilla media","Final media","CSI medio","Ops","Rel","Dev","Puntos F1GOAT (GP)"], True, mapping)
tcols = ["Equipo","Parrilla media","Final media","CSI medio","Ops","Rel","Dev","Puntos F1GOAT (GP)"]
tview = tview[tcols].sort_values("Puntos F1GOAT (GP)", ascending=False).copy()
tview.index = pd.RangeIndex(1, len(tview)+1, name="Pos")
st.subheader("Constructores — GP (F1GOAT)")
st.dataframe(tview, use_container_width=True, height=auto_table_height(len(tview)))
