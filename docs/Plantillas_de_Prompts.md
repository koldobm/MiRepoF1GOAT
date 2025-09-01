# Plantillas de Prompts F1GOAT (mejoradas)

## [INICIAR PROYECTO: ESQUELETO]
Genera el esqueleto del proyecto F1GOAT en ~/F1GOAT con:
1) Comandos para crear venv y dependencias mínimas (pandas, duckdb, streamlit, fastf1).
2) Estructura de carpetas y archivos (con contenido) mediante bloques Bash con heredocs.
3) app.py y pages/ con la UI de pestañas: Último GP, Temporada, Histórico Pilotos, Mejores Temporadas, Metodología.
4) f1goat/*.py con funciones stub/TODOs y firmas claras.
5) config/lineage.yaml con ejemplos de linaje.
ENTREGA en ORDEN DE EJECUCIÓN para copiar/pegar en terminal.

## [INSTALAR Y ARRANCAR]
Dame comandos para:
- Activar el venv y (re)instalar dependencias.
- Lanzar la app con: streamlit run app.py
- URL local para abrir en el navegador y cómo detener/relanzar.

## [ACTUALIZACIÓN AUTOMÁTICA]
Crea el servicio y timer systemd (usuario) que ejecute `python -m f1goat update` cada martes 09:00 (Europa/Madrid).
- Incluye los archivos .service y .timer con heredocs.
- Comandos para habilitar, arrancar el timer y verificar el próximo disparo.

## [LANZADOR .desktop]
Genera `~/.local/share/applications/f1goat.desktop` que abra la app.
- Usa un icono en `app/assets/f1goat.png` (si no existe, crea un placeholder).
- Incluye el comando para actualizar la base de datos de lanzadores.

## [IMPLEMENTAR ÚLTIMO GP]
Rellena compute.py y storage.py para:
- Calcular CSI básico, cap por distancia y combinar componentes disponibles (omitir OQ/WA si no hay datos).
- Guardar/leer datos en DuckDB (data/f1goat.duckdb).
- Mostrar en la pestaña “Último GP” las 2 tablas (pilotos y constructores) y el bloque “Cómo se calcula”.
Incluye pruebas con datos simulados si aún no hay ingestión real.

## [IMPLEMENTAR TEMPORADA]
Añade el escalado a 0–100 (SeasonCap) y los gráficos de evolución (pilotos y equipos).
- Asegúrate de recalcular SeasonCap cuando se cancelen GPs.
- Tablas ordenables por cualquier columna.

## [HISTÓRICO Y EB]
Implementa el ranking histórico (1950→) por “Media de puntos por GP (AJUSTADA EB)”.
- Define y calcula el parámetro k según la varianza observada.
- Muestra columnas indicadas y, opcional, bandas de incertidumbre.

## [LINAJES TOGGLE]
Implementa el toggle “Agrupar linajes de equipo”:
- ON: mapear constructores a linaje según config/lineage.yaml y agrupar puntuaciones.
- OFF: mostrar por nombre oficial anual.
Devuélveme el diff de código, el punto donde se lee el YAML y una prueba simple.

## [CHEQUEO RÁPIDO]
Dame un checklist para validar tras cada GP:
- ¿Se detecta el último GP disputado?
- ¿Se recalcula CSI/residuales/puntuaciones y se graba en DuckDB?
- ¿Tablas del Último GP y Temporada reflejan los nuevos datos?
- ¿SeasonCap ajustado si hubo cancelaciones/acortamientos?
- ¿Funciona el toggle de linajes y la ordenación por cabeceras?

## [BOTÓN ACTUALIZAR AHORA]
Añade a app.py un botón “Actualizar ahora” (header):
- Al pulsarlo, llama a la misma función que `python -m f1goat update` (o invoca el módulo).
- Muestra feedback (spinner, éxito/fracaso) y recarga tablas.
Devuélveme el bloque de código completo con la import y la llamada, usando try/except y un mensaje en la UI.

## [PERSISTENCIA DEL TIMER]
Quiero instrucciones para asegurar que la actualización se ejecute aunque el PC estuviera apagado o sin sesión iniciada:
1) Explica `Persistent=true` del timer.
2) Da el comando para habilitar lingering: `loginctl enable-linger "$USER"`.
3) Indica cómo comprobar próximos disparos y el último run.
Devuélvelo con comandos listos para copiar/pegar.

