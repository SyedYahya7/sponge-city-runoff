"""Command-line entry point: python -m spongecity.cli --help"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .rational import run_scenario, summarize


def make_figure(results: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = range(len(results))
    w = 0.38
    ax.bar([i - w / 2 for i in x], results.runoff_baseline_m3yr / 1e3, w, label="Baseline")
    ax.bar([i + w / 2 for i in x], results.runoff_post_m3yr / 1e3, w, label="Post-LID")
    ax.set_xticks(list(x))
    ax.set_xticklabels(results.class_name, rotation=25, ha="right")
    ax.set_ylabel("Annual runoff (thousand m$^3$/yr)")
    ax.set_title("Annual runoff by land class: baseline vs. Sponge City scenario")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", default="data/landuse_scenarios.csv")
    p.add_argument("--outdir", default="results")
    p.add_argument("--rainfall", type=float, default=0.95, help="annual rainfall, m/yr")
    p.add_argument("--intensity", type=float, default=None,
                   help="design storm intensity, mm/hr (adds peak discharge in m3/s)")
    p.add_argument("--wells", type=int, default=10, help="number of recharge wells")
    p.add_argument("--well-capacity", type=float, default=9500.0, help="m3/yr per well")
    p.add_argument("--no-overrides", action="store_true",
                   help="ignore c_new_override and blend every class")
    args = p.parse_args(argv)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    landuse = pd.read_csv(args.input)
    results = run_scenario(
        landuse, args.rainfall, args.intensity, use_overrides=not args.no_overrides
    )
    summary = summarize(results, args.wells, args.well_capacity)

    results.to_csv(outdir / "runoff_results.csv", index=False)
    pd.Series(summary).to_csv(outdir / "summary.csv", header=["value"])
    make_figure(results, outdir / "runoff_comparison.png")

    print(results[["class_name", "c_baseline", "c_new",
                   "runoff_baseline_m3yr", "runoff_post_m3yr", "reduction_pct"]]
          .round(3).to_string(index=False))
    print()
    for k, v in summary.items():
        print(f"{k:28s} {v:,.3f}")
    print(f"\nOutputs written to {outdir}/")


if __name__ == "__main__":
    main()
