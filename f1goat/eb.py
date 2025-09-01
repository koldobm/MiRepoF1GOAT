from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Tuple

def estimate_k_eb(points: pd.DataFrame, group_col: str, value_col: str) -> Tuple[float, float]:
    """
    Estima k para w = n/(n+k) con método-de-momentos:
      - var_between ≈ varianza entre medias de grupo
      - var_within  ≈ varianza intra-grupo
      k ≈ var_within / var_between
    Devuelve (k, mu_global).
    """
    df = points.dropna(subset=[group_col, value_col]).copy()
    if df.empty:
        return 1.0, 0.0
    mu = df[value_col].mean()

    # estadísticas por grupo
    g = df.groupby(group_col)[value_col].agg(['count', 'mean', 'var']).rename(columns={'count':'n','mean':'m','var':'s2'})
    g = g.fillna({'s2': 0.0})
    n_total = int(g['n'].sum())
    g_count = int(g.shape[0])
    if n_total <= g_count:
        return 1.0, mu

    # Between y Within (ANOVA simple)
    var_between = float(np.sum(g['n'] * (g['m'] - mu)**2) / max(n_total - 1, 1))
    var_within = float(np.sum((g['n'] - 1).clip(lower=0) * g['s2']) / max(n_total - g_count, 1))

    if var_between <= 1e-12:
        return 1.0, mu
    k = max(var_within / var_between, 1e-6)
    return float(k), float(mu)

def eb_adjust_means(points: pd.DataFrame, group_col: str, value_col: str) -> pd.DataFrame:
    """
    Devuelve DataFrame con columnas:
      group_col, n, mean, eb_mean  (media ajustada EB)
    """
    k, mu = estimate_k_eb(points, group_col, value_col)
    g = points.groupby(group_col)[value_col].agg(['count','mean']).rename(columns={'count':'n','mean':'mean'}).reset_index()
    g['eb_w'] = g['n'] / (g['n'] + k)
    g['eb_mean'] = g['eb_w'] * g['mean'] + (1.0 - g['eb_w']) * mu
    return g[[group_col, 'n', 'mean', 'eb_mean']]
