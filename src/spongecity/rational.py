"""Core hydrology functions.

Method (Rational Method, Q = C * i * A):
  * Annual runoff volume (m3/yr) = C * annual_rainfall (m/yr) * area (m2)
  * Peak discharge (m3/s)        = C * i (mm/hr) * area (m2) / 3.6e6
  * Scenario coefficient for a land class that is partly retrofitted:
        C_new = (1 - r) * C_baseline + r * C_lid
    where r is the fraction of the class treated with LID.
"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = {
    "class_name",
    "area_m2",
    "c_baseline",
    "c_lid",
    "intervention_ratio",
}


def blend_coefficient(c_baseline: float, c_lid: float, ratio: float) -> float:
    """Area-weighted runoff coefficient for a partly retrofitted land class."""
    if not 0.0 <= ratio <= 1.0:
        raise ValueError(f"intervention ratio must be in [0, 1], got {ratio}")
    return (1.0 - ratio) * c_baseline + ratio * c_lid


def annual_runoff_volume(c: float, rainfall_m_per_yr: float, area_m2: float) -> float:
    """Annual runoff volume in m3/yr."""
    return c * rainfall_m_per_yr * area_m2


def peak_discharge(c: float, intensity_mm_per_hr: float, area_m2: float) -> float:
    """Peak discharge in m3/s. 1 mm/hr over 1 m2 = 1e-3 m3 / 3600 s."""
    return c * intensity_mm_per_hr * area_m2 / 3.6e6


def run_scenario(
    landuse: pd.DataFrame,
    rainfall_m_per_yr: float = 0.95,
    intensity_mm_per_hr: float | None = None,
    use_overrides: bool = True,
) -> pd.DataFrame:
    """Compute baseline and post-LID runoff for every land class.

    Parameters
    ----------
    landuse : table with the columns in REQUIRED_COLUMNS. An optional
        ``c_new_override`` column replaces the blended coefficient where filled.
    rainfall_m_per_yr : annual rainfall depth (m/yr).
    intensity_mm_per_hr : design storm intensity; if given, peak discharge
        columns (m3/s) are added.
    use_overrides : set False to ignore ``c_new_override`` and use the
        blending formula for every class.
    """
    missing = REQUIRED_COLUMNS - set(landuse.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")

    df = landuse.copy()
    df["c_new"] = [
        blend_coefficient(cb, cl, r)
        for cb, cl, r in zip(df.c_baseline, df.c_lid, df.intervention_ratio)
    ]
    if use_overrides and "c_new_override" in df.columns:
        df["c_new"] = df["c_new_override"].fillna(df["c_new"])

    df["runoff_baseline_m3yr"] = [
        annual_runoff_volume(c, rainfall_m_per_yr, a)
        for c, a in zip(df.c_baseline, df.area_m2)
    ]
    df["runoff_post_m3yr"] = [
        annual_runoff_volume(c, rainfall_m_per_yr, a)
        for c, a in zip(df.c_new, df.area_m2)
    ]
    df["reduction_pct"] = 100.0 * (
        1.0 - df.runoff_post_m3yr / df.runoff_baseline_m3yr
    )

    if intensity_mm_per_hr is not None:
        df["q_baseline_m3s"] = [
            peak_discharge(c, intensity_mm_per_hr, a)
            for c, a in zip(df.c_baseline, df.area_m2)
        ]
        df["q_post_m3s"] = [
            peak_discharge(c, intensity_mm_per_hr, a)
            for c, a in zip(df.c_new, df.area_m2)
        ]
    return df


def summarize(
    results: pd.DataFrame,
    n_wells: int = 0,
    well_capacity_m3yr: float = 9500.0,
) -> dict:
    """Campus totals, composite coefficients and recharge-well adjustment."""
    total_area = results.area_m2.sum()
    base = results.runoff_baseline_m3yr.sum()
    post = results.runoff_post_m3yr.sum()
    recharge = n_wells * well_capacity_m3yr
    final = post - recharge
    return {
        "total_area_m2": total_area,
        "composite_c_baseline": (results.c_baseline * results.area_m2).sum() / total_area,
        "composite_c_post": (results.c_new * results.area_m2).sum() / total_area,
        "runoff_baseline_m3yr": base,
        "runoff_post_lid_m3yr": post,
        "recharge_wells_m3yr": recharge,
        "runoff_final_m3yr": final,
        "reduction_lid_only_pct": 100.0 * (1.0 - post / base),
        "reduction_final_pct": 100.0 * (1.0 - final / base),
    }
