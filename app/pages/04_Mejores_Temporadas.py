import os, sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from f1goat.compute import auto_table_height
from f1goat.aggregations import best_seasons_pilots, best_seasons_teams
from f1goat.naming import load_lineages, apply_lineage_grouping
from f1goat.ui import render_legend

st.set_page_config(page_title="F1GOAT — Mejores Temporadas", page_icon="app/assets/f1goat.png", layout="wide")
st.title("📚 Mejores Temporadas")
render_legend(["mejores_temporadas"])

col1, col2 = st.columns(2)

with col1:
    st.subheader("Pilotos — media por temporada")
    dp = best_seasons_pilots()
    if dp.empty:
        st.info("Sin datos suficientes. Amplía el backfill (ej.: 2018→).")
    else:
        st.dataframe(dp, use_container_width=True, height=auto_table_height(len(dp)))

with col2:
    st.subheader("Constructores — media por temporada")
    dt = best_seasons_teams()
    if dt.empty:
        st.info("Sin datos suficientes. Amplía el backfill (ej.: 2018→).")
    else:
        # Respetar toggle de linajes si aplica
        mapping = load_lineages()
        if st.sidebar.checkbox("Agrupar linajes de equipo", value=False, key="lineage_best"):
            dt = apply_lineage_grouping(dt, "Equipo", ["GPs media","Temps. disputadas","Media por temporada"], False, mapping)
        st.dataframe(dt, use_container_width=True, height=auto_table_height(len(dt)))
