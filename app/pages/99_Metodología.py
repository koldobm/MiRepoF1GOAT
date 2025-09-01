import streamlit as st

st.set_page_config(page_title="F1GOAT — Metodología", page_icon="app/assets/f1goat.png", layout="wide")
st.title("ℹ️ Metodología (detallada)")

st.markdown(r"""
## 0) Nomenclatura y siglas

**RR** *(Race pace/result)*, **QR** *(Qualifying)*, **TD** *(Tyre/long-run Dynamics)*,  
**OQ** *(Overtaking Quality)*, **WA** *(Wet Ability)*, **PF** *(Penalty Factor)*,  
**CSI** *(Contextual Skill Index)*, **Ops** *(Operaciones)*, **Rel** *(Fiabilidad)*, **Dev** *(Desarrollo)*.

Todas las métricas de rendimiento (RR, QR, TD, OQ, WA, CSI, Ops, Rel, Dev) se expresan en **[0, 10]**.

---

## 1) Puntos F1GOAT (pilotos) por GP — **máx. 10**

Pesos por defecto (**constantes**):  
- \(w_{RR}=5\), \(w_{QR}=2\), \(w_{TD}=1.5\), \(w_{OQ}=1\), \(w_{WA}=0.5\).  
Si falta un componente (por era/condición), **renormalizamos** con los presentes para que el **máximo siga siendo 10**.

\[
\text{Base} = 10 \times \frac{\sum_{i \in \mathcal{C}} c_i \, w_i}{10 \times \sum_{i \in \mathcal{C}} w_i}
\qquad
\text{Puntos GP} = \max\!\big(0, \min(10,\, \text{Base} - \text{PF})\big)
\]

- \(\mathcal{C}\) = subconjunto de componentes **disponibles** en el GP.  
- \(\text{PF} \in [0,2]\) y se **resta** (se trunca a 2 si excede).  
- Esta forma garantiza **equidad entre eras**: si no hay OQ/WA, el máximo alcanzable sigue siendo **10**.

**Cálculo de componentes (fuente de datos real):**
- **RR:** ritmo de carrera (delta vs mediana del campo por vuelta), posición final corregida por incidentes, consistencia.  
- **QR:** delta de vuelta rápida de quali vs mediana de Q3/Q2 (según pase), posiciones de parrilla.  
- **TD:** degradación, consistencia en tandas largas, ejecución de stint/undercut/overcut.  
- **OQ:** oportunidades de adelantamiento **creadas y convertidas** (intentos limpios, no DNF), ponderadas por dificultad.  
- **WA:** rendimiento relativo en vueltas/sectores marcados como mojado.  

En el esqueleto se usan valores simulados; en producción, estas señales vienen de telemetría/laps y eventos por GP.

---

## 2) **CSI** — Contextual Skill Index (mérito relativo)

Medimos el mérito **descontando o bonificando** por la fuerza del coche (\(\text{car\_strength}\)):

\[
\textbf{CSI} = \frac{\text{media}\big(\{RR,QR,TD[,OQ][,WA]\}_{\text{disponibles}}\big)}{\text{car\_strength}}
\]

- \(\text{car\_strength} > 1\) ⇒ coche **fuerte** ⇒ divide por >1 ⇒ **rebaja** el valor.  
- \(\text{car\_strength} < 1\) ⇒ coche **débil** ⇒ divide por <1 ⇒ **bonifica**.

**Estimación de car\_strength (resumen):**
1) **Ritmo relativo** del equipo: \(\Delta_{\text{pace}} = \text{median\_lap}_{team} - \text{median\_lap}_{field}\) (normalizado).  
2) **Escala**: \(\text{car\_strength} = 1 + \alpha \cdot \Delta_{\text{pace}}\), con límites, p. ej. \([0.85, 1.20]\).  
3) **Ajustes** por fiabilidad (DNF no atribuible al piloto) y distribución de stints.

---

## 3) Constructores — Puntos por GP (**0–10**)

Se combinan métricas de equipo:

\[
\textbf{Puntos GP (constructor)} = 0.6\cdot \text{CSI medio} + 0.2\cdot \text{Ops} + 0.1\cdot \text{Rel} + 0.1\cdot \text{Dev}
\]

- **CSI medio:** media del CSI de los pilotos del equipo en el GP.  
- **Ops (0–10):** efectividad en paradas, estrategia (undercut/overcut), ejecución sin errores.  
- **Rel (0–10):** fiabilidad (DNF técnicos, fallos de pit, penalizaciones mecánicas).  
- **Dev (0–10):** evolución del coche a lo largo del año (upgrades que mejoran ritmo sostenidamente).

Si faltara una señal, **renormalizamos** los pesos sobre las presentes.

---

## 4) Temporada — **SeasonCap (0–100) absoluto**

El tope teórico de una temporada con \(N_{GP}\) pruebas es \(10 \times N_{GP}\).  

\[
\text{SeasonCap} = 100 \times \frac{\text{Acum}}{10 \times N_{GP}}
\]

- Ej.: 5 GP y **5 puntos por GP** ⇒ \(25/50 \times 100 = 50\).  
- Así, incluso dominando cada GP **sin llegar a 10**, el tope **no es 100** salvo perfección absoluta.

---

## 5) Histórico — **EB (Empirical Bayes / shrinkage)**

Para medias por GP en carreras largas/cortas:

\[
w = \frac{n}{n + k},\quad
\mu_{\text{ajustada}} = w \cdot \mu_{\text{muestral}} + (1-w)\cdot \mu_{\text{población}}
\]

- \(n\): tamaño de muestra (GPs del piloto).  
- \(k\): hiperparámetro (suaviza hacia la media poblacional).  
- Reduce varianza en pilotos con pocas carreras.

---

## 6) Reglas y detalles de implementación

- **Indexado**: tablas con índice **desde 1**, sin columna “Pos” duplicada.  
- **Ordenación**: por **Puntos F1GOAT (GP)** en GP; por **SeasonCap** o **Total GP** en temporada.  
- **Linajes**: agrupación opcional (`config/lineage.yaml`) p. ej., *Benetton→Renault→Alpine*.  
- **Desambiguación**: pilotos con homónimos → sufijo “(n. AAAA)”.  
- **Nombre oficial del GP**: siempre “Nombre oficial + año”.  
- **Redondeos**: mostramos 2–3 decimales para legibilidad.

---

## 7) Ejemplo numérico (seco, sin OQ/WA)

RR=9.2, QR=8.5, TD=8.0, PF=0.3, \(w=\{5,2,1.5\}\).  
\[
\text{Base} = 10 \times \frac{9.2\cdot5 + 8.5\cdot2 + 8.0\cdot1.5}{10\cdot(5+2+1.5)} = 8.78
\]
\(\text{Puntos GP}=8.78-0.3=8.48\).  
Si \(\text{car\_strength}=1.10\) ⇒ \(\text{CSI}=\frac{(9.2+8.5+8.0)/3}{1.10}=7.78\).

---
""")
