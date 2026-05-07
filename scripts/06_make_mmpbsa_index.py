#!/usr/bin/env python3
"""
Generate gmx_MMPBSA index file defining Receptor and Ligand groups.
Uses MDAnalysis to identify protein and ligand atom indices.
"""

import argparse
from pathlib import Path


def make_index(tpr: str, resname: str, output: str) -> None:
    try:
        import MDAnalysis as mda
    except ImportError:
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "MDAnalysis"])
        import MDAnalysis as mda

    u = mda.Universe(tpr)

    receptor = u.select_atoms("protein")
    ligand   = u.select_atoms(f"resname {resname}")

    if len(receptor) == 0:
        raise ValueError("No protein atoms found. Check the TPR file.")
    if len(ligand) == 0:
        raise ValueError(f"No atoms with resname '{resname}' found. Adjust --resname.")

    print(f"[06] Receptor: {len(receptor)} atoms | Ligand ({resname}): {len(ligand)} atoms")

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        f.write("[ Receptor ]\n")
        indices = " ".join(str(i + 1) for i in receptor.indices)  # 1-based
        for chunk in [indices[i:i+15] for i in range(0, len(indices.split()), 15)]:
            f.write(" ".join(str(x) for x in chunk.split()) + "\n")

        f.write("\n[ Ligand ]\n")
        indices = " ".join(str(i + 1) for i in ligand.indices)
        for chunk in [indices[i:i+15] for i in range(0, len(indices.split()), 15)]:
            f.write(" ".join(str(x) for x in chunk.split()) + "\n")

    print(f"[06] Index written → {output}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tpr",     required=True)
    parser.add_argument("--resname", required=True)
    parser.add_argument("--output",  required=True)
    args = parser.parse_args()
    make_index(args.tpr, args.resname, args.output)


if __name__ == "__main__":
    main()
