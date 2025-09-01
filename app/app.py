import os, sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
from f1goat.ui import render_legend
from f1goat.naming import load_lineages, apply_lineage_grouping
from f1goat.simdata import simulate_gp
from f1goat.storage import load_latest_gp, get_latest_calendar_event, get_latest_results_event
from f1goat.compute import auto_table_height
from f1goat import update as update_now

st.set_page_config(page_title="F1GOAT", page_icon="app/assets/f1goat.png", layout="wide")

# Sidebar: toggles
if "group_lineage" not in st.session_state:
    st.session_state["group_lineage"] = False
st.sidebar.header("⚙️ Opciones")
st.session_state["group_lineage"] = st.sidebar.checkbox("Agrupar linajes de equipo", value=st.session_state["group_lineage"])
real_only = st.sidebar.checkbox("Solo datos reales (sin simulación)", value=bool(int(os.environ.get("F1GOAT_REAL_ONLY","0"))))

# Header + botón
c1, c2 = st.columns([1, 0.25])
with c1: st.title("F1GOAT — Análisis F1")
with c2:
    if st.button("🔄 Actualizar ahora", use_container_width=True):
        with st.spinner("Ingeriendo último GP real (puede tardar la primera vez)…"):
            ok = update_now()
        st.success("Actualización completada.") if ok else st.error("Fallo en actualización.")
        st.rerun()

# Aviso de GP nuevo en calendario sin resultados en DB
cal = get_latest_calendar_event()
res = get_latest_results_event()
if cal and (not res or pd.to_datetime(cal["date"]) > pd.to_datetime(res["date"])):
    st.warning(f"Hay un evento más reciente en el calendario: **{cal['official_name']}** (R{cal['round']}). Pulsa **Actualizar ahora** para intentar ingerirlo.")

# Leyenda
render_legend(["gp_drivers","gp_teams"])

tabs = st.tabs(["🏁 Gran Premio", "📊 Temporada", "👑 Histórico Pilotos", "📚 Mejores Temporadas", "ℹ️ Metodología"])

# === SOLO último GP (real si hay; si 'solo reales' y no hay, muestra error) ===
with tabs[0]:
    drivers = teams = None
    gp_title = None
    try:
        d_real, t_real, gp_name_real, season_real, rnd_real = load_latest_gp()
        if d_real is not None and not d_real.empty:
            gp_title = gp_name_real
            drivers = d_real
            teams = t_real
    except Exception as e:
        st.warning(f"Fuente real no disponible: {e}")

    if drivers is None or teams is None:
        if real_only:
            st.error("Modo 'solo datos reales' activo y no hay datos en la base. Ejecuta “Actualizar ahora” o `python -m f1goat update/backfill`.")
            st.stop()
        season, rnd = 2025, 22
        drivers, teams, gp_title = simulate_gp(season, rnd)

    st.markdown(f"### {gp_title}")

    cols = ["Piloto","Equipo","Parrilla","Final","CSI","RR","QR","TD","OQ","WA","PF","Puntos F1GOAT (GP)"]
    dview = drivers[cols].sort_values("Puntos F1GOAT (GP)", ascending=False).copy()
    dview.index = pd.RangeIndex(1, len(dview)+1, name="Pos")
    st.subheader("Pilotos — GP (F1GOAT)")
    st.dataframe(dview, use_container_width=True, height=auto_table_height(len(dview)))

    mapping = load_lineages()
    tview = teams.copy()
    if st.session_state["group_lineage"]:
        tview = apply_lineage_grouping(tview, "Equipo",
            ["Parrilla media","Final media","CSI medio","Ops","Rel","Dev","Puntos F1GOAT (GP)"], True, mapping)
    tview = tview[["Equipo","Parrilla media","Final media","CSI medio","Ops","Rel","Dev","Puntos F1GOAT (GP)"]]\
            .sort_values("Puntos F1GOAT (GP)", ascending=False).copy()
    tview.index = pd.RangeIndex(1, len(tview)+1, name="Pos")
    st.subheader("Constructores — GP (F1GOAT)")
    st.dataframe(tview, use_container_width=True, height=auto_table_height(len(tview)))

with tabs[1]:
    st.info("Usa la página **Gran Premio** para navegar por cualquier GP. La pestaña **Temporada** está en su propia página.")

with tabs[2]:
    st.info("Abre **Histórico Pilotos** (página lateral) para ver los agregados reales de toda la historia disponible.")

with tabs[3]:
    st.info("Abre **Mejores Temporadas** (página lateral) para ver los rankings de temporadas (pilotos y constructores).")

with tabs[4]:
    st.markdown("Consulta la página **Metodología** para detalles matemáticos.")
