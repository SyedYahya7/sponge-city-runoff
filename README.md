# sponge-city-runoff

Rational Method runoff model for a Sponge City (Low Impact Development) scenario analysis.
It computes annual runoff volume and optional peak discharge for a campus, before and after
LID retrofits, and reports the combined effect of groundwater recharge wells.

The inputs come from my final-year design project, *An Appraisal of a Sponge City Design for
NUST H-12 Main Campus* (NUST Islamabad, 2026): a 707-acre campus, six land-cover classes from a
supervised GIS classification, and PMD annual rainfall of 950 mm/yr.

## Method

| Quantity | Equation |
|---|---|
| Annual runoff volume (m³/yr) | `V = C · P · A` (P = annual rainfall in m/yr, A in m²) |
| Peak discharge (m³/s) | `Q = C · i · A / 3.6e6` (i in mm/hr, A in m²) |
| Post-LID coefficient for a partly retrofitted class | `C_new = (1 − r)·C_baseline + r·C_lid` |
| Composite coefficient | `C_w = Σ(C_x · A_x) / A_total` |
| Recharge wells | `V_final = V_post − n_wells · capacity` |

`r` is the fraction of the class treated with LID (e.g. 0.60 of road length with bioswales).

## Quick start

```bash
git clone https://github.com/<SyedYahya7>/sponge-city-runoff.git
cd sponge-city-runoff
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
python -m spongecity.cli                    # annual volumes, uses data/landuse_scenarios.csv
python -m spongecity.cli --intensity 50     # also computes peak discharge at 50 mm/hr
pytest                                      # 7 tests
```

Outputs go to `results/`: `runoff_results.csv`, `summary.csv`, `runoff_comparison.png`.

## Using your own data

Edit or replace `data/landuse_scenarios.csv`. Columns:

`class_name, area_m2, c_baseline, c_lid, intervention_ratio, c_new_override`

Leave `c_new_override` empty to use the blending formula. Pass `--no-overrides` to ignore it.
Other flags: `--rainfall`, `--wells`, `--well-capacity`, `--input`, `--outdir`.

## Reproducing the thesis

With the default data file the model reproduces the thesis tables:

| Quantity | Thesis | This code |
|---|---|---|
| Baseline runoff (Table 4.2) | 2.56 million m³/yr | 2,561,075 m³/yr |
| Post-LID runoff (Table 4.3) | 1.83 million m³/yr | 1,835,697 m³/yr |
| After 10 recharge wells | 1.74 million m³/yr | 1,740,697 m³/yr |
| Total reduction | 32.03 % | 32.03 % |

## Two inconsistencies found while writing this code

Re-implementing the calculation exposed two issues in the thesis tables. Both are kept
visible rather than silently fixed.

1. **Acre-to-m² conversion.** The thesis table converts acres to m² with a factor of 10,000
   (the hectare factor). One acre is 4,046.86 m². Every area, and therefore every runoff volume,
   is overstated by a factor of 2.47. Percent reductions per class are unaffected, but the
   recharge wells (95,000 m³/yr, an absolute volume) take a larger share of a smaller total.
   `data/landuse_scenarios_acre_corrected.csv` uses the correct conversion:

   | | Thesis units | Corrected units |
   |---|---|---|
   | Baseline runoff | 2,561,075 m³/yr | 1,036,430 m³/yr |
   | After 10 wells | 1,740,697 m³/yr | 647,880 m³/yr |
   | Total reduction | 32.03 % | 37.49 % |

2. **Road coefficient.** The blending formula reproduces every post-LID coefficient in
   Table 4.3 except roads: `0.4·0.90 + 0.6·0.25 = 0.51`, but the thesis reports 0.4125. The default
   data file carries 0.4125 as an explicit override so the thesis totals reproduce. Run with
   `--no-overrides` to use 0.51.

## Layout

```
src/spongecity/rational.py   core functions (blend, volume, peak discharge, scenario, summary)
src/spongecity/cli.py        command-line interface and figure
data/                        land-use tables (thesis units and acre-corrected)
tests/test_rational.py       checks against thesis Tables 4.2, 4.3 and the 32.03 % result
```

## Limitations

The Rational Method assumes uniform rainfall over the catchment and a fixed coefficient per
land class. It does not route flow, model infiltration dynamics or simulate storage. It is a
screening-level tool, suited to comparing scenarios rather than sizing drainage.

## License

MIT
