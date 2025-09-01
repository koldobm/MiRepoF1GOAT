import os, pathlib, pandas as pd, streamlit as st
from f1goat.storage import coverage_table

st.set_page_config(layout="wide")
st.title("Diagnóstico de datos")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Estado de fuentes")
    blocked = os.getenv("F1GOAT_BLOCK_ERGAST","0").lower() in ("1","true","yes")
    st.write(f"**Ergast**: {'🚫 bloqueado por entorno' if blocked else '✅ habilitado'}")
    st.write("**FastF1**: ✅ habilitado")
with col2:
    st.subheader("Ficheros y BD")
    db = pathlib.Path("data/f1goat.duckdb")
    st.write(f"Base de datos: **{db}** {'(existe ✅)' if db.exists() else '(no existe ❌)'}")
    log = pathlib.Path("data/ingest_log.csv")
    st.write(f"Ingest log: **{log}** {'(existe ✅)' if log.exists() else '(no existe ❌)'}")

st.subheader("Cobertura por temporada")
st.dataframe(coverage_table(), use_container_width=True)
if pathlib.Path("data/ingest_log.csv").exists():
    st.subheader("Últimas entradas de ingesta")
    df = pd.read_csv("data/ingest_log.csv")
    df = df.sort_values(["season","round"], ascending=[False,False]).tail(100)
    st.dataframe(df, use_container_width=True)
