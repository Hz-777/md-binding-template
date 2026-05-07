#!/usr/bin/env python3
"""
Protein preparation: remove non-standard residues, fix missing atoms/residues,
add hydrogens at physiological pH, write clean PDB for GROMACS.
Requires: pdbfixer, openmm
"""

import sys
import argparse
from pathlib import Path


def prepare_protein(input_pdb: str, output_pdb: str, ph: float = 7.4) -> None:
    try:
        from pdbfixer import PDBFixer
        from openmm.app import PDBFile
    except ImportError:
        sys.exit("ERROR: pdbfixer / openmm not installed. Run: conda install -c conda-forge pdbfixer openmm")

    print(f"[01] Loading {input_pdb}")
    fixer = PDBFixer(filename=input_pdb)

    print("[01] Finding missing residues and atoms …")
    fixer.findMissingResidues()
    fixer.findNonstandardResidues()
    fixer.replaceNonstandardResidues()
    fixer.removeHeterogens(keepWater=False)   # strip ligands, waters, ions
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(ph)

    Path(output_pdb).parent.mkdir(parents=True, exist_ok=True)
    with open(output_pdb, "w") as f:
        PDBFile.writeFile(fixer.topology, fixer.positions, f)
    print(f"[01] Wrote clean protein → {output_pdb}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  default="inputs/protein.pdb")
    parser.add_argument("--output", default="work/01_protein_clean.pdb")
    parser.add_argument("--ph",     type=float, default=7.4)
    args = parser.parse_args()
    prepare_protein(args.input, args.output, args.ph)


if __name__ == "__main__":
    main()
