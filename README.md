# F1GOAT — v1.0

Metodología estable para evaluar pilotos (0–10 por GP) y equipos (0–10 por GP) con comparabilidad inter-eras.

## Resumen rápido
- **Pilotos**: `Total_GP = min(cap, m(c) * (RR + QR + TD + OQ))`
  - `cap = 10 * %distancia completada`
  - `m(c)` modula por **CSI** (fuerza del coche), acotado; **WA/PF no suman**
- **Equipos**: `Total_GP = CSI* (0–5) + Ops (0–2) + Strat (0–2) + Dev (0–1)`
- **SeasonCap**: se reescala cada temporada a 100 puntos

## Documentación
- `docs/Metodologia_v1.0.md`
- `exports/Metodologia_v1.0.rendered.md`
- Manifest de exportables: `exports/manifest_v1.json`

## Datos exportados clave
- `season_driver_points_100.csv`, `season_team_points_100.csv`
- `per_gp_core_for_ui.csv`
- Overlays de auditoría v1.1: `per_gp_*_overlay_v1_1.csv` (no afectan puntuación)

## Estado de la app
- La app muestra **v1.0** (tablas/vistas `*_v1_100_ui` y `per_gp_core_for_ui`)
- Los **overlays v1.1** son informativos para auditoría
