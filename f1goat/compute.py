"""
Cálculos oficiales F1GOAT (simulación):
- Puntos por GP (máx. 10) con pesos: RR=5, QR=2, TD=1.5, OQ=1, WA=0.5.
- Renormalización por era (si faltan OQ/WA).
- CSI: índice de mérito ajustado por fuerza del coche (car_strength >= 0).
- SeasonCap a 0–100.
"""
from dataclasses import dataclass
from typing import Iterable, Optional
import pandas as pd

@dataclass(frozen=True)
class WeightsGP:
    RR: float = 5.0
    QR: float = 2.0
    TD: float = 1.5
    OQ: float = 1.0
    WA: float = 0.5
    PF_max_penalty: float = 2.0  # penalización máxima absoluta

def _safe(val: Optional[float]) -> Optional[float]:
    return None if val is None else float(val)

def compute_gp_points_f1goat(
    rr: Optional[float]=None, qr: Optional[float]=None, td: Optional[float]=None,
    oq: Optional[float]=None, wa: Optional[float]=None, pf: float=0.0,
    w: WeightsGP = WeightsGP()
) -> float:
    """
    Cada componente se expresa en escala 0–10 (placeholder). Puntuación final 0–10.
    - Se incluyen solo los componentes presentes y se renormaliza para que el máximo posible siga siendo 10.
    - PF se interpreta como penalización (>=0); se trunca a PF_max_penalty.
    """
    parts = []
    weights = []
    if rr is not None: parts.append(_safe(rr)); weights.append(w.RR)
    if qr is not None: parts.append(_safe(qr)); weights.append(w.QR)
    if td is not None: parts.append(_safe(td)); weights.append(w.TD)
    if oq is not None: parts.append(_safe(oq)); weights.append(w.OQ)
    if wa is not None: parts.append(_safe(wa)); weights.append(w.WA)

    if not parts:
        base = 0.0
    else:
        weighted = sum(p * wt for p, wt in zip(parts, weights))
        max_if_all_ten = 10.0 * sum(weights)
        base = 10.0 * (weighted / max_if_all_ten)

    penalty = max(0.0, min(abs(pf), w.PF_max_penalty))
    score = max(0.0, min(10.0, base - penalty))
    return float(round(score, 3))

def compute_csi(
    rr: Optional[float]=None, qr: Optional[float]=None, td: Optional[float]=None,
    oq: Optional[float]=None, wa: Optional[float]=None, car_strength: float=1.0
) -> float:
    """
    CSI (mérito contextual): media de componentes disponibles (0–10) ajustada por fuerza de coche.
    CSI = media_componentes / max(car_strength, eps)
    - car_strength ~ 1.0 = coche medio; >1 coche fuerte; <1 coche débil.
    """
    eps = 1e-6
    comps = [x for x in [rr, qr, td, oq, wa] if x is not None]
    base = (sum(comps) / len(comps)) if comps else 0.0
    csi = base / max(car_strength, eps)
    return float(round(csi, 3))

def season_scale_0_100(series: Iterable[float]) -> pd.Series:
    s = pd.Series(series, dtype="float64")
    if s.empty:
        return s
    lo, hi = s.min(), s.max()
    if hi == lo:
        return pd.Series([100.0]*len(s), index=s.index)
    return (s - lo) * 100.0 / (hi - lo)

def auto_table_height(n_rows: int, row_px: int = 35, header_px: int = 40, max_px: int = 900) -> int:
    return min(max_px, header_px + row_px * max(1, n_rows))
