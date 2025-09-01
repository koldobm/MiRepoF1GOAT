import os, sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from f1goat.compute import auto_table_height
from f1goat.aggregations import historical_pilots_table
from f1goat.ui import render_legend

st.set_page_config(page_title="F1GOAT — Histórico Pilotos", page_icon="app/assets/f1goat.png", layout="wide")
st.title("👑 Histórico Pilotos")
render_legend(["historico_pilotos"])

df = historical_pilots_table()
if df.empty:
    st.warning("No hay datos históricos suficientes en la base. Ejecuta backfill para más temporadas (ej.: `python -m f1goat backfill --from 2018 --to 2025`).")
else:
    st.dataframe(df, use_container_width=True, height=auto_table_height(len(df)))
