import os, sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
from f1goat.ui import render_legend
from f1goat.naming import load_lineages, apply_lineage_grouping
from f1goat.simdata import simulate_season
from f1goat.storage import list_seasons, load_season
from f1goat.compute import auto_table_height

st.set_page_config(page_title="F1GOAT — Temporada", page_icon="app/assets/f1goat.png", layout="wide")
st.title("📊 Temporada")
render_legend(["season_drivers","season_teams"])

# Sidebar: toggles
if "group_lineage" not in st.session_state:
    st.session_state["group_lineage"] = False
st.sidebar.header("⚙️ Opciones")
st.session_state["group_lineage"] = st.sidebar.checkbox("Agrupar linajes de equipo", value=st.session_state["group_lineage"])
real_only = st.sidebar.checkbox("Solo datos reales (sin simulación)", value=False)

# Selección de temporada (DB si hay, si no rango completo)
db_seasons = list_seasons()
season = st.selectbox("Temporada", db_seasons if db_seasons else list(range(2025, 1950-1, -1)), index=0)

# Intentar datos reales
d_rounds, t_rounds, d_final, t_final = load_season(season)

# Fallback si la DB no tiene esa temporada
if d_rounds.empty or t_rounds.empty:
    if real_only:
        st.error("Modo 'solo datos reales' activo y no hay datos en la base para esta temporada.")
        st.stop()
    # Simulación (8 rondas demo)
    d_rounds, t_rounds, d_final, t_final = simulate_season(season, rounds=8)

# === Pilotos: Tabla (agregada) + Gráfico ===
st.subheader("Pilotos — acumulado de temporada (cap absoluto)")
dcols = ["Piloto","Equipo","Parrilla media","Final media","CSI medio","RR medio","QR medio","TD medio","OQ medio","WA medio","PF medio","Total GP","Acum 0–100"]
dtab = d_final[dcols].sort_values("Acum 0–100", ascending=False).copy()
dtab.index = pd.RangeIndex(1, len(dtab)+1, name="Pos")
st.dataframe(dtab, use_container_width=True, height=auto_table_height(len(dtab)))

st.markdown("**Gráfico — Pilotos (SeasonCap 0–100 por GP)**")
piv_d = d_rounds.pivot(index="Ronda", columns="Piloto", values="Acum 0–100").sort_index()
st.line_chart(piv_d, use_container_width=True)

# === Constructores: Tabla (agregada) + Gráfico ===
st.subheader("Constructores — acumulado de temporada (cap absoluto)")
mapping = load_lineages()
ttab = t_final.copy()
if st.session_state.get("group_lineage", False) and not ttab.empty:
    ttab = apply_lineage_grouping(ttab, "Equipo",
        ["Parrilla media","Final media","CSI medio","Ops","Rel","Dev","Total GP","Acum","Acum 0–100"],
        True, mapping)
tcols = ["Equipo","Parrilla media","Final media","CSI medio","Ops","Rel","Dev","Total GP","Acum 0–100"]
ttab = ttab[tcols].sort_values("Acum 0–100", ascending=False).copy()
ttab.index = pd.RangeIndex(1, len(ttab)+1, name="Pos")
st.dataframe(ttab, use_container_width=True, height=auto_table_height(len(ttab)))

st.markdown("**Gráfico — Constructores (SeasonCap 0–100 por GP)**")
piv_t = t_rounds.pivot(index="Ronda", columns="Equipo", values="Acum 0–100").sort_index()
st.line_chart(piv_t, use_container_width=True)

with st.expander("📐 Cómo se calcula (Temporada)"):
    st.markdown("""
**Cap absoluto 0–100**: `Acum / (10 × nº GP)` × 100.  
**Pilotos (tabla)**: `CSI medio` entre **Final media** y **RR medio**; `Total GP` = suma de puntos por GP.  
**Constructores (tabla)**: `Equipo`, `Parrilla media`, `Final media`, **`CSI medio`**, `Ops`, `Rel`, `Dev`, `Total GP`, `Acum 0–100`.  
Con linajes ON, se agrupa por `config/lineage.yaml` (tabla).
""")
