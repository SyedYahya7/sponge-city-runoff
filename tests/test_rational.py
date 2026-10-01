import pandas as pd
import pytest

from spongecity import blend_coefficient, peak_discharge, run_scenario, summarize

LANDUSE = pd.read_csv("data/landuse_scenarios.csv")


def test_blend_coefficient_matches_thesis_rows():
    assert blend_coefficient(0.85, 0.40, 0.70) == pytest.approx(0.535)
    assert blend_coefficient(0.20, 0.10, 0.30) == pytest.approx(0.17)
    assert blend_coefficient(0.35, 0.20, 0.15) == pytest.approx(0.3275)
    assert blend_coefficient(0.45, 0.20, 0.40) == pytest.approx(0.35)


def test_blend_rejects_bad_ratio():
    with pytest.raises(ValueError):
        blend_coefficient(0.5, 0.2, 1.5)


def test_baseline_total_matches_table_4_2():
    res = run_scenario(LANDUSE)
    assert res.runoff_baseline_m3yr.sum() == pytest.approx(2_561_073, rel=1e-4)


def test_post_lid_total_matches_table_4_3():
    res = run_scenario(LANDUSE)
    assert res.runoff_post_m3yr.sum() == pytest.approx(1_835_697, rel=1e-4)


def test_final_reduction_with_wells_is_32_percent():
    s = summarize(run_scenario(LANDUSE), n_wells=10, well_capacity_m3yr=9500)
    assert s["runoff_final_m3yr"] == pytest.approx(1_740_697, rel=1e-4)
    assert s["reduction_final_pct"] == pytest.approx(32.03, abs=0.01)


def test_peak_discharge_units():
    # C=1, 1 mm/hr over 1 km2 = 1000 m3/hr = 0.2778 m3/s
    assert peak_discharge(1.0, 1.0, 1e6) == pytest.approx(1000 / 3600)


def test_blending_everywhere_changes_roads_only():
    a = run_scenario(LANDUSE, use_overrides=True)
    b = run_scenario(LANDUSE, use_overrides=False)
    diff = a.c_new.round(6) != b.c_new.round(6)
    assert list(a.class_name[diff]) == ["Roads"]
    assert b.c_new[0] == pytest.approx(0.51)
