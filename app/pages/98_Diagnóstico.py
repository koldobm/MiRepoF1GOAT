import os, sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
from f1goat.storage import load_latest_gp, _debug_summary
from f1goat.compute import auto_table_height

st.set_page_config(page_title="F1GOAT — Diagnóstico", page_icon="app/assets/f1goat.png", layout="wide")
st.title("🩺 Diagnóstico de datos (DB)")

st.code(_debug_summary())

d, t, name, season, rnd = load_latest_gp()
if d is None or t is None:
    st.error("No hay datos reales aún en la base. Ejecuta 'Actualizar ahora' o `python -m f1goat update`.")
    st.stop()

st.markdown(f"### Último evento: {name} — season={season}, round={rnd}")

st.subheader("Pilotos (head)")
h = d.head(10).copy()
h.index = pd.RangeIndex(1, len(h)+1, name="Pos")
st.dataframe(h, use_container_width=True, height=auto_table_height(len(h)))

st.subheader("Constructores (head)")
ht = t.head(10).copy()
ht.index = pd.RangeIndex(1, len(ht)+1, name="Pos")
st.dataframe(ht, use_container_width=True, height=auto_table_height(len(ht)))

st.caption("Si algo no cuadra, comparte esta pantalla o usa `python -m f1goat validate`.")
