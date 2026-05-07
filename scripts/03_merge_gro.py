#!/usr/bin/env python3
"""Merge two GROMACS .gro files (protein + ligand) into one complex.gro."""

import argparse
from pathlib import Path


def parse_gro(path: str):
    lines = Path(path).read_text().splitlines()
    title = lines[0]
    n_atoms = int(lines[1].strip())
    atom_lines = lines[2:2 + n_atoms]
    box = lines[2 + n_atoms]
    return title, n_atoms, atom_lines, box


def merge_gro(prot_path: str, lig_path: str, out_path: str) -> None:
    _, n_prot, prot_atoms, box = parse_gro(prot_path)
    _, n_lig,  lig_atoms,  _   = parse_gro(lig_path)

    total = n_prot + n_lig

    # Renumber atoms sequentially
    merged_atoms = []
    for i, line in enumerate(prot_atoms + lig_atoms, start=1):
        # GRO format: cols 0-4 resnum, 5-9 resname, 10-14 atomname, 15-19 atomnum
        merged_atoms.append(line[:15] + f"{i:5d}" + line[20:])

    out_lines = [
        "Protein-Ligand Complex",
        f"{total:5d}",
        *merged_atoms,
        box,
    ]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(out_lines) + "\n")
    print(f"[03] Merged {n_prot} protein + {n_lig} ligand atoms → {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protein", required=True)
    parser.add_argument("--ligand",  required=True)
    parser.add_argument("--output",  required=True)
    args = parser.parse_args()
    merge_gro(args.protein, args.ligand, args.output)


if __name__ == "__main__":
    main()
