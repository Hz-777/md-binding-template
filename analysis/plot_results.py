#!/usr/bin/env python3
"""
Plot MD analysis results:
 - RMSD (protein backbone, ligand)
 - Energy (potential, temperature, pressure)
 - MM-PB/GBSA binding free energy breakdown
"""

import subprocess
import sys
import re
from pathlib import Path

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
except ImportError:
    sys.exit("ERROR: matplotlib not installed")


MDDIR   = Path("work/05_md")
OUTDIR  = Path("results/plots")
OUTDIR.mkdir(parents=True, exist_ok=True)


def run_gmx_energy(term: str, edr: str, xvg: str) -> np.ndarray | None:
    """Extract energy term from .edr via gmx energy."""
    result = subprocess.run(
        ["gmx", "energy", "-f", edr, "-o", xvg],
        input=term + "\n0\n",
        capture_output=True, text=True
    )
    if result.returncode != 0 or not Path(xvg).exists():
        return None
    return load_xvg(xvg)


def load_xvg(path: str) -> np.ndarray:
    """Load GROMACS XVG file, skip comment lines."""
    data = []
    for line in Path(path).read_text().splitlines():
        if line.startswith(("#", "@")):
            continue
        row = list(map(float, line.split()))
        if row:
            data.append(row)
    return np.array(data)


def compute_rmsd(tpr: str, xtc: str, selection: str, output_xvg: str) -> np.ndarray | None:
    """Compute RMSD via gmx rms."""
    # selection: "Backbone" or "LIG" group number/name
    result = subprocess.run(
        ["gmx", "rms", "-s", tpr, "-f", xtc, "-o", output_xvg, "-tu", "ns"],
        input=f"{selection}\n{selection}\n",
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"WARNING: gmx rms failed for {selection}: {result.stderr[:200]}")
        return None
    return load_xvg(output_xvg)


def parse_mmpbsa_results(dat_path: str) -> dict:
    """Parse FINAL_RESULTS_MMPBSA.dat for energy components."""
    text = Path(dat_path).read_text()
    results = {}
    pattern = re.compile(
        r"(VDWAALS|EEL|EGB|EPB|ESURF|ECAVITY|DELTA G binding)\s+=\s+([-\d.]+)\s+\+/-\s+([-\d.]+)"
    )
    for m in pattern.finditer(text):
        term, mean, std = m.group(1), float(m.group(2)), float(m.group(3))
        results[term] = (mean, std)
    return results


def plot_rmsd():
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    for ax, (sel, label, color) in zip(axes, [
        ("Backbone", "Protein Backbone RMSD", "royalblue"),
        ("4",        "Ligand RMSD",           "tomato"),
    ]):
        xvg = str(OUTDIR / f"rmsd_{label.split()[0].lower()}.xvg")
        data = compute_rmsd(str(MDDIR / "md.tpr"), str(MDDIR / "md.xtc"), sel, xvg)
        if data is not None:
            ax.plot(data[:, 0], data[:, 1] * 10, color=color, lw=1.2)  # nm → Å
            ax.set_ylabel("RMSD (Å)", fontsize=12)
            ax.set_title(label, fontsize=13)
            ax.axhline(np.mean(data[:, 1]) * 10, ls="--", color="gray", lw=0.8, label=f"Mean={np.mean(data[:, 1])*10:.2f} Å")
            ax.legend(fontsize=10)
            ax.grid(alpha=0.3)
        else:
            ax.text(0.5, 0.5, "Data not available", transform=ax.transAxes, ha="center")

    axes[-1].set_xlabel("Time (ns)", fontsize=12)
    fig.suptitle("MD Trajectory RMSD", fontsize=14, fontweight="bold")
    plt.tight_layout()
    out = OUTDIR / "rmsd.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"[plot] Saved {out}")


def plot_mmpbsa():
    dat = Path("results/mmpbsa/FINAL_RESULTS_MMPBSA.dat")
    if not dat.exists():
        print("[plot] MM-PBSA results not found, skipping.")
        return

    results = parse_mmpbsa_results(str(dat))
    if not results:
        print("[plot] Could not parse MM-PBSA results.")
        return

    labels = list(results.keys())
    means  = [results[k][0] for k in labels]
    stds   = [results[k][1] for k in labels]
    colors = ["steelblue" if v < 0 else "tomato" for v in means]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(labels, means, xerr=stds, color=colors, alpha=0.8,
                   error_kw={"elinewidth": 1.5, "capsize": 4})
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("Energy (kcal/mol)", fontsize=12)
    ax.set_title("MM-PB/GBSA Energy Decomposition", fontsize=13, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)

    for bar, val, std in zip(bars, means, stds):
        ax.text(val + (1 if val >= 0 else -1), bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}±{std:.1f}", va="center", fontsize=9)

    plt.tight_layout()
    out = OUTDIR / "mmpbsa_decomposition.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"[plot] Saved {out}")

    # Print summary
    dg = results.get("DELTA G binding")
    if dg:
        print(f"\n{'='*50}")
        print(f"  ΔG binding = {dg[0]:.2f} ± {dg[1]:.2f} kcal/mol")
        print(f"  Ki (estimated) ≈ {1e9 * np.exp(dg[0] / 0.592):.1f} nM  (at 300 K)")
        print(f"{'='*50}\n")


if __name__ == "__main__":
    print("[analysis] Generating RMSD plots …")
    plot_rmsd()
    print("[analysis] Generating MM-PB/GBSA plots …")
    plot_mmpbsa()
    print(f"[analysis] All plots saved to {OUTDIR}/")
