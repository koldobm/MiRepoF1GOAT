from typing import Iterable

def _bullets(items: Iterable[str]) -> str:
    return "\n".join(f"- {x}" for x in items)

def render_legend(contexts: list[str] | None = None):
    import streamlit as st
    contexts = contexts or []

    st.markdown("""
**Leyenda / Siglas (común)**
- **RR**: Rendimiento en carrera (0–10).
- **QR**: Rendimiento en clasificación (0–10).
- **TD**: Gestión/ritmo de tanda (0–10).
- **OQ**: Oportunidades de adelantamiento aprovechadas (0–10, solo eras con dato).
- **WA**: Actuación en mojado (0–10, solo si hay lluvia).
- **PF**: Penalización (0–2) que **resta**.
- **Puntos F1GOAT (GP)** *(piloto/constructor)*: mezcla ponderada renormalizada a **máx. 10** (menos PF).
- **CSI (piloto)**: media de componentes **ajustada por fuerza del coche** (coche fuerte ⇒ divide >1; débil ⇒ divide <1).
- **Constructores**: **0.6·CSI medio + 0.2·Ops + 0.1·Rel + 0.1·Dev** (0–10).
- **SeasonCap (0–100)** *(absoluto)*: `Acum / (10 × nº GP)` × 100.
- **Linajes**: con el toggle activo, se agrupan equipos según `config/lineage.yaml`.
""")

    if "gp_drivers" in contexts:
        st.markdown("**Cabeceros — Pilotos (Gran Premio)**")
        st.markdown(_bullets([
            "**Piloto**: nombre completo.",
            "**Equipo**: constructor con el que disputa el GP.",
            "**Parrilla**: posición de salida.",
            "**Final**: posición final.",
            "**CSI**: mérito contextual del piloto en este GP.",
            "**RR/QR/TD/OQ/WA**: componentes (0–10).",
            "**PF**: penalización total del GP (0–2).",
            "**Puntos F1GOAT (GP)**: puntuación del GP (define la posición, máx. 10).",
        ]))

    if "gp_teams" in contexts:
        st.markdown("**Cabeceros — Constructores (Gran Premio)**")
        st.markdown(_bullets([
            "**Equipo**: nombre oficial del constructor.",
            "**Parrilla media**: media de las posiciones de salida de sus coches.",
            "**Final media**: media de las posiciones finales.",
            "**CSI medio**: media del CSI de sus pilotos en el GP.",
            "**Ops**: operaciones de equipo (paradas, estrategia) (0–10).",
            "**Rel**: fiabilidad (0–10).",
            "**Dev**: desarrollo del coche (0–10).",
            "**Puntos F1GOAT (GP)**: 0.6·CSI medio + 0.2·Ops + 0.1·Rel + 0.1·Dev.",
        ]))

    if "season_drivers" in contexts:
        st.markdown("**Cabeceros — Pilotos (Temporada)**")
        st.markdown(_bullets([
            "**Piloto/Equipo**: identidad.",
            "**Parrilla media / Final media**: medias de la temporada.",
            "**CSI medio**: entre **Final media** y **RR medio**; mérito contextual promedio.",
            "**RR/QR/TD/OQ/WA/PF medios**: medias por GP.",
            "**Total GP**: suma de Puntos F1GOAT (GP) en la temporada.",
            "**Acum 0–100**: SeasonCap absoluto (`Acum/(10×GP)×100`).",
        ]))

    if "season_teams" in contexts:
        st.markdown("**Cabeceros — Constructores (Temporada)**")
        st.markmarkdown = st.markdown  # alias
        st.markdown(_bullets([
            "**Equipo**: nombre del constructor.",
            "**Parrilla media / Final media**: medias en la temporada.",
            "**CSI medio**: después de **Final media**.",
            "**Ops/Rel/Dev**: medias en la temporada.",
            "**Total GP**: suma de Puntos F1GOAT (GP) por GP.",
            "**Acum 0–100**: SeasonCap absoluto.",
        ]))

    if "historical_drivers" in contexts:
        st.markdown("**Cabeceros — Histórico Pilotos**")
        st.markdown(_bullets([
            "**Piloto**: nombre completo.",
            "**Equipos y años**: `Equipo (rango, ..., año suelto, ...)` — puede haber varios equipos en un mismo año.",
            "**GPs**: grandes premios disputados.",
            "**Parrilla/Final medias**: medias globales.",
            "**CSI medio**: siempre después de **Final media**.",
            "**Media por GP (AJUSTADA)**: ajuste empírico EB (shrinkage).",
            "**Total acumulado**: suma histórica de puntos F1GOAT.",
        ]))

    if "best_seasons_pilots" in contexts or "best_seasons_teams" in contexts:
        st.markdown("**Cabeceros — Mejores Temporadas**")
        st.markdown(_bullets([
            "**Piloto / Equipo**: identidad.",
            "**Equipos (años)** *(solo pilotos)*: `Equipo (rango, años sueltos)` dentro de la temporada.",
            "**GPs media**: **media** de GP disputados por temporada.",
            "**Temps. disputadas**: nº de temporadas del piloto/equipo.",
            "**1º (años) / 2º (años) / 3º (años)**: **conteo** y, entre paréntesis, **los años** (p. ej., `4 (1972–1974, 1980)`).",
            "**Total / Media por temporada**: acumulados y promedios.",
        ]))
