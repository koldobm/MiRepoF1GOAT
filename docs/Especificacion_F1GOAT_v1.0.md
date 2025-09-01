# Especificación F1GOAT v1.0 (ampliada)

## 0) UI y navegación
- Pestañas: Último GP, Temporada, Histórico Pilotos, Mejores Temporadas, Metodología.
- Tablas ordenables por click; selector de Temporada y GP (por defecto, último GP disputado).
- Mostrar siempre un bloque “Cómo se calcula” con fórmulas de cap, CSI y combinaciones de puntuación.
- Toggle **“Agrupar linajes de equipo”** (ON/OFF):
  - OFF: cada constructor por su nombre oficial del año.
  - ON: se agrupan puntuaciones a nivel de **linaje** según `config/lineage.yaml`.
- Header con botón “Actualizar ahora”. Al pulsarlo, ejecuta la rutina de actualización y recarga datos.
- Al arrancar, si hay datos pendientes, mostrar un banner “Datos nuevos disponibles — Actualizar ahora”.


## 1) Definiciones clave
- QPI, RPI, CSI, cap: (idéntico al bloque B anterior).
- Residuales y componentes de piloto: RR 50%, QR 20%, TD 15%, OQ 10% (moderno), WA 5%; PF hasta −2.0.
- Componentes de constructor: 60% CSI, 20% Operaciones, 10% Fiabilidad, 10% Desarrollo.
- Temporada: SeasonCap = Σ cap; Totales 0–100.
- Eras: percentiles; filtros SC/VSC; sprints integrados; omitir OQ/WA donde no haya datos.

## 2) Columnas de tablas
- Último GP – Pilotos: Pos | Piloto | Equipo | CSI | Parrilla | Final | RR | QR | TD | OQ? | WA? | PF | **Puntos GP**
- Último GP – Constructores: Pos | Equipo | CSI | Ops | Rel | Dev | **Puntos GP**
- Temporada – Pilotos: Pos | Piloto | Equipo principal | CSI medio | Parrilla media | Final media | RR | QR | TD | OQ? | WA? | PF | **Total 0–100**
- Temporada – Constructores: Pos | Equipo | CSI medio | Parrilla media | Final media | Ops | Rel | Dev | **Total 0–100**
- Histórico Pilotos: Pos | Piloto | Equipos y años | GPs | Parrilla media | Final media | RR | QR | TD | OQ? | WA? | **Total acumulado** | **Media por GP (AJUSTADA)**
- Mejores Temporadas – Pilotos: Pos | Piloto | Equipos (años) | GPs temp. | Temps. disputadas | 1º (años) | 2º (años) | 3º (años) | Total carrera | **Media por temporada**
- Mejores Temporadas – Equipos: Pos | Equipo | GPs | Temps. disputadas | 1º (años) | 2º (años) | 3º (años) | Total | **Media por temporada**

## 3) Desambiguación y nombres
- Pilotos: nombre completo; si hay homónimos, añadir “(n. AAAA)”.
- GPs: “YYYY — Nombre oficial completo”.
- Constructores: nombre oficial anual; con toggle ON, usar linaje definido en `config/lineage.yaml`.

## 4) Media por GP histórica (ajustada EB)
- `media_ajustada = w·media_muestral + (1−w)·media_población`, con `w = n/(n+k)` y `k` estimado de datos.
- Mostrar opcionalmente bandas de incertidumbre.

## 5) Linajes de equipos (ejemplos; editable)
Archivo `config/lineage.yaml`:
```yaml
Renault_Alpine:
  - Benetton
  - Renault
  - Lotus F1 Team
  - Alpine
Aston_Martin:
  - Jordan
  - Midland
  - Spyker
  - Force India
  - Racing Point
  - Aston Martin
Mercedes:
  - Tyrrell
  - BAR
  - Honda
  - Brawn GP
  - Mercedes
RB:
  - Minardi
  - Toro Rosso
  - AlphaTauri
  - RB
Sauber_Stake:
  - Sauber
  - BMW Sauber
  - Alfa Romeo F1 Team
  - Stake F1 Team

