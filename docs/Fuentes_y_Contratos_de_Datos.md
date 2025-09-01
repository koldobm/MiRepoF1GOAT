1) OpenF1 (moderno, ≈2018→): 
   - Datos: vueltas, telemetría, radio, estado de pista, boxes, stints, adelantamientos (beta), sesiones, metadatos. Históricos sin auth; tiempo real requiere cuenta.
   - Formatos: JSON/CSV; filtros por fecha y por “session_key” (acepta “latest”).
   - Uso: OQ (adelantamientos on-track), WA (segmentos wet), RPI (ritmo carrera), QPI (quali), boxes/estrategia.

2) FastF1 (lib. Python):
   - 2018→: timing/telemetría/tyres/weather/track status.
   - 1950→: calendario y resultados (vía interfaz Ergast-compat/jolpica-f1).
   - Cache local; devuelve DataFrames listos para análisis.

3) FIA (PDFs oficiales por GP):
   - “Race Classification”, “Stewards’ Decisions”, “Pit Stop Summary” ► verdad de sanciones/causas DNF y boxes.
   - Usar como autoridad para penalizaciones (PF) y cierres de clasificación.

4) Notas de estabilidad:
   - Ergast original quedó deprecado tras 2024; FastF1 documenta soporte Ergast-compat mediante jolpica-f1. 
   - OpenF1 documenta endpoints y ejemplos con salidas JSON, y aclara que el histórico es libre, el live es de pago.
