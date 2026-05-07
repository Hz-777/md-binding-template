#!/usr/bin/env python3
"""
Patch GROMACS topol.top to include ligand .itp and add ligand molecule entry.
Inserts #include statements and appends the ligand to [ molecules ].
"""

import argparse
import re
from pathlib import Path


def patch_topology(topol: str, lig_itp: str, lig_name: str, posres_lig: str) -> None:
    text = Path(topol).read_text()

    # Insert ligand itp after the last forcefield include
    lig_include = f'\n; Ligand parameters\n#include "{Path(lig_itp).resolve()}"\n'
    posres_include = (
        f'\n; Ligand position restraints\n'
        f'#ifdef POSRES_LIG\n'
        f'#include "{Path(posres_lig).resolve()}"\n'
        f'#endif\n'
    )

    # Find where to insert: after the last #include in the header block
    ff_include_pattern = re.compile(r'(#include\s+".*?\.itp"[^\n]*\n)(?!\s*#include)', re.MULTILINE)
    match = list(re.finditer(r'#include\s+".*?"', text))
    if not match:
        raise ValueError("No #include lines found in topology — unexpected format.")

    insert_pos = match[-1].end() + text[match[-1].end():].index("\n") + 1
    text = text[:insert_pos] + lig_include + posres_include + text[insert_pos:]

    # Append ligand to [ molecules ] section
    if lig_name not in text.split("[ molecules ]")[-1]:
        text = text.rstrip() + f"\n{lig_name}             1\n"

    Path(topol).write_text(text)
    print(f"[03] Patched {topol} with ligand {lig_name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topol",      required=True)
    parser.add_argument("--lig-itp",    required=True)
    parser.add_argument("--lig-name",   required=True)
    parser.add_argument("--posres-lig", required=True)
    args = parser.parse_args()
    patch_topology(args.topol, args.lig_itp, args.lig_name, args.posres_lig)


if __name__ == "__main__":
    main()
