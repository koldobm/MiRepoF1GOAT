# Metodología F1GOAT (v1.0)

## Resumen
- **Pilotos (0–10 por GP)**:  
  ```
  Total_GP = min(cap, m_eff * (RR + QR + TD + OQ))
  ```
  **WA/PF no suman** (se muestran aparte).
- **Constructores (0–10 por GP)**:  
  ```
  Total_GP = CSI*_0-5 + Ops_0-2 + Strat_0-2 + Dev_0-1
  ```
- **SeasonCap = 100** con GPs efectivos. **NA no redistribuye**.

## CSI (fuerza de coche)
```
CSI_z  = alpha * Z(QPT) + beta * Z(RPT)                         # moderna/intermedia
CSI_z  = gamma * Z(QualyPercentil) + (1-gamma) * Z(BT_rating)   # clásica
CSI*   = exp(lambda * CSI_z)   # media≈1.00 por GP; rango ~[0.85,1.15]
```

## Modulación por CSI en pilotos
```
c     = CSI*_equipo / media_GP(CSI*)
m(c)  = clip(c^(-alpha), m_min, m_max)   # alpha≈0.33, m_min=0.85, m_max=1.20
u in [0,1]  # calidad de datos
m_eff = 1 + (m(c) - 1) * u
Total_GP = min(cap, m_eff * (RR + QR + TD + OQ))
```

## Cap por GP
```
cap = 10 * porcentaje_distancia
# v1.0 fallback: cap=10 si faltan L_plan y D_plan (log explícito)
# caso extremo: si carrera 100% neutralizada -> cap=0
```

## OQ (adelantamientos) con datos pobres — GPC
```
Clasificados = pilotos que acaban
R0 = parrilla entre clasificados
R1 = llegada entre clasificados
GPC = max(0, R0 - R1)
# Oportunidades: factor eta in [0.8,1.0] si mucha SC/VSC
# Con expectativa: GPC_resid = max(0, E[R] - R1)
```

## CSI* a 0–5 para constructores (método A recomendado)
```
x_i = ln(CSI*_i)
z_i = (x_i - median(x)) / max(MAD(x), 1e-6)
score_i = 5 * Phi(z_i)   # Phi = CDF Normal estándar
si MAD=0 -> score_i = 2.5
```

## WA y PF (no suman)
- **WA**: índice de habilidad en mojado (0–0.5 normalizado). Visible y con ranking “Rain Master”.
- **PF**: índice de penalizaciones/errores (>=0 normalizado). Visible y con ranking “Clean Driver”.
- En eras/GP sin dato: **NA** (no 0). No se modulan por CSI.

## Calidad de datos (u)
```
u = 0.3*quali + 0.4*race_laps + 0.2*(banderas/lluvia) + 0.1*intra_equipo
# si solo mejor vuelta en carrera: race_laps=0.2
# truncar u a [0,1]
```

## Reglas de justicia
- NA no redistribuye; CSI en pilotos solo modula; en equipos sí puntúa.
- SeasonCap=100 con GPs efectivos; cap por distancia por GP.
