#!/usr/bin/env python3
"""
Ligand parameterization: SDF/MOL2 → GROMACS topology via acpype.
Generates GAFF2 force field parameters with AM1-BCC charges.
Requires: acpype, rdkit, openbabel
"""

import subprocess
import sys
import argparse
import shutil
from pathlib import Path


def sdf_to_mol2(sdf_path: str, mol2_path: str) -> None:
    """Convert SDF to MOL2 using RDKit (preserves 3D coordinates)."""
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
    except ImportError:
        sys.exit("ERROR: rdkit not found. Run: conda install -c conda-forge rdkit")

    mol = Chem.MolFromMolFile(sdf_path, removeHs=False)
    if mol is None:
        sys.exit(f"ERROR: Cannot parse {sdf_path}. Check file format.")

    # Add Hs if missing
    mol = Chem.AddHs(mol)
    if mol.GetNumConformers() == 0:
        AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
        AllChem.MMFFOptimizeMolecule(mol)

    writer = Chem.MolToMolFile  # fallback: obabel
    Chem.MolToMolFile(mol, mol2_path.replace(".mol2", ".sdf"))
    # Use obabel for proper MOL2 with charges
    result = subprocess.run(
        ["obabel", mol2_path.replace(".mol2", ".sdf"), "-O", mol2_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        sys.exit(f"ERROR: obabel failed:\n{result.stderr}")


def run_acpype(mol2_path: str, charge: int, ff: str, work_dir: str) -> str:
    """Run acpype to generate GROMACS topology files."""
    if not shutil.which("acpype"):
        sys.exit("ERROR: acpype not found. Run: conda install -c conda-forge acpype")

    Path(work_dir).mkdir(parents=True, exist_ok=True)
    cmd = [
        "acpype",
        "-i", str(Path(mol2_path).resolve()),
        "-c", "bcc",          # AM1-BCC charges
        "-f", "mol2",
        "-a", ff,             # gaff or gaff2
        "-n", str(charge),
        "-o", "gmx",
        "-d",                 # direct output
    ]
    print(f"[02] Running acpype: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        sys.exit(f"ERROR: acpype failed:\n{result.stderr}")

    # acpype creates a directory named <basename>.acpype
    base = Path(mol2_path).stem
    acpype_dir = Path(work_dir) / f"{base}.acpype"
    if not acpype_dir.exists():
        sys.exit(f"ERROR: Expected acpype output dir {acpype_dir} not found.")
    print(f"[02] acpype output → {acpype_dir}")
    return str(acpype_dir)


def copy_gmx_files(acpype_dir: str, dest_dir: str) -> None:
    """Copy .itp and .gro files needed by GROMACS to work/ligand/."""
    base = Path(acpype_dir).stem.replace(".acpype", "")
    Path(dest_dir).mkdir(parents=True, exist_ok=True)

    for suffix in ["_GMX.itp", "_GMX.gro", "_GMX_OPLS.itp"]:
        src = Path(acpype_dir) / f"{base}{suffix}"
        if src.exists():
            dst = Path(dest_dir) / src.name
            shutil.copy(src, dst)
            print(f"[02] Copied {src.name} → {dest_dir}")

    # Write position restraint itp for ligand
    posres_itp = Path(dest_dir) / "posres_lig.itp"
    posres_itp.write_text(
        "; Ligand position restraints\n"
        "#ifdef POSRES_LIG\n"
        "[ position_restraints ]\n"
        "; atom  type  fx    fy    fz\n"
        "  1     1     1000  1000  1000\n"
        "#endif\n"
    )
    print(f"[02] Wrote {posres_itp}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",   default="inputs/ligand.sdf")
    parser.add_argument("--charge",  type=int, default=0, help="Net charge of ligand")
    parser.add_argument("--ff",      default="gaff2", choices=["gaff", "gaff2"])
    parser.add_argument("--workdir", default="work/02_ligand")
    args = parser.parse_args()

    mol2_path = str(Path(args.workdir) / "ligand.mol2")
    Path(args.workdir).mkdir(parents=True, exist_ok=True)

    print(f"[02] Converting {args.input} → MOL2")
    sdf_to_mol2(args.input, mol2_path)

    acpype_dir = run_acpype(mol2_path, args.charge, args.ff, args.workdir)
    copy_gmx_files(acpype_dir, "work/02_ligand/gmx")
    print("[02] Ligand preparation complete.")


if __name__ == "__main__":
    main()
