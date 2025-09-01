# Plan de Ejecución (Runbook)

Fase 0 — Preparación
- Crear carpeta de trabajo: ~/F1GOAT
- Crear entorno Python (venv) e instalar dependencias mínimas: pandas, duckdb, streamlit, fastf1
- (Más adelante) Añadir parsers OpenF1 y FIA-PDF en la Fase 2

Fase 1 — Esqueleto de código
- Estructura de carpetas: app/, app/pages/, app/f1goat/, data/, config/, docs/
- Archivos mínimos:
  - app/app.py (UI principal Streamlit)
  - app/pages/01_Último_GP.py, 02_Temporada.py, 03_Histórico_Pilotos.py, 04_Mejores_Temporadas.py, 99_Metodología.py
  - app/f1goat/{data_sources.py, compute.py, models.py, storage.py, naming.py, cli.py}
  - config/lineage.yaml (linajes de equipos)
- Implementar: CSI básico, residuales mínimos, tablas de “Último GP” y “Temporada” (pueden empezar con datos simulados)

Fase 2 — Datos modernos y FIA
- Integrar OQ (adelantamientos) y WA (mojado) para era moderna (≈2018→)
- Integrar “Operaciones” (pit/estrategia) desde PDFs oficiales FIA
- Añadir caché y lógica de ingestión incremental en data_sources.py
- Re-normalización automática de pesos cuando falte un componente por era

Fase 3 — Automatización y lanzador
- Crear servicio y timer systemd (usuario) que ejecute: python -m f1goat update
  - Programación: martes 09:00 (Europa/Madrid)
- Crear lanzador .desktop que abra la app (streamlit run app.py)
- Checklist de verificación tras cada actualización

Fase 4 — Histórico y EB
- Tabla histórica (1950→) con ranking por “Media de puntos por GP (AJUSTADA EB)”
  - Empirical Bayes: media_ajustada = w·media_muestral + (1−w)·media_población; w = n/(n+k)
  - Estimar k de los datos; mostrar bandas de incertidumbre (opcional)
- “Mejores Temporadas” (pilotos y equipos) con media por temporada (0–100)
- Toggle “Agrupar linajes de equipo” operativo en toda la app

Entrega de instrucciones (estándar)
- Siempre dar comandos para copiar/pegar en Arch (Bash), en orden
- Para escribir archivos: usar heredocs (cat <<'EOF' > ruta … EOF)
- Al final de cada fase: incluir prueba rápida de verificación

