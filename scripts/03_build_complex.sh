#!/usr/bin/env bash
# Build protein-ligand complex topology for GROMACS.
# Input:  work/01_protein_clean.pdb, work/02_ligand/gmx/
# Output: work/03_complex/{topol.top, complex.gro, index.ndx}
set -euo pipefail

WORKDIR="work/03_complex"
LIGDIR="work/02_ligand/gmx"
PROTEIN_PDB="work/01_protein_clean.pdb"

mkdir -p "$WORKDIR"

# Detect ligand base name (e.g. MOL_GMX.itp → MOL)
LIG_ITP=$(ls "$LIGDIR"/*_GMX.itp 2>/dev/null | grep -v OPLS | head -1)
LIG_GRO=$(ls "$LIGDIR"/*_GMX.gro 2>/dev/null | head -1)
if [[ -z "$LIG_ITP" || -z "$LIG_GRO" ]]; then
    echo "ERROR: No ligand GMX files found in $LIGDIR"; exit 1
fi
LIG_BASE=$(basename "$LIG_ITP" _GMX.itp)
echo "[03] Ligand base name: $LIG_BASE"

# --- 1. Generate protein topology ---
echo "[03] Running pdb2gmx on protein …"
gmx pdb2gmx \
    -f "$PROTEIN_PDB" \
    -o "$WORKDIR/protein.gro" \
    -p "$WORKDIR/topol.top" \
    -i "$WORKDIR/posres.itp" \
    -ff charmm36m \
    -water tip3p \
    -ignh \
    -missing \
    -quiet

# --- 2. Combine protein + ligand GRO ---
echo "[03] Merging protein and ligand coordinates …"
python3 - <<'PYEOF'
import sys, re
from pathlib import Path

prot_gro = Path("work/03_complex/protein.gro")
lig_gro  = Path(sys.argv[1]) if len(sys.argv) > 1 else None

prot_lines = prot_gro.read_text().splitlines()
n_prot     = int(prot_lines[1].strip())
prot_atoms  = prot_lines[2 : 2 + n_prot]
box_line    = prot_lines[-1]

import subprocess, shlex
lig_gro_path = "$(ls work/02_ligand/gmx/*_GMX.gro | head -1)"
PYEOF

# Simpler: use editconf + gmx trick
python3 scripts/03_merge_gro.py \
    --protein "$WORKDIR/protein.gro" \
    --ligand  "$LIG_GRO" \
    --output  "$WORKDIR/complex.gro"

# --- 3. Patch topology to include ligand itp ---
echo "[03] Patching topology …"
python3 scripts/03_patch_topology.py \
    --topol   "$WORKDIR/topol.top" \
    --lig-itp "$LIG_ITP" \
    --lig-name "$LIG_BASE" \
    --posres-lig "$LIGDIR/posres_lig.itp"

# --- 4. Build index file ---
echo "[03] Creating index groups …"
# Create combined Protein_LIG group
printf "q\n" | gmx make_ndx \
    -f "$WORKDIR/complex.gro" \
    -o "$WORKDIR/index.ndx" \
    -quiet

echo "[03] Complex topology built → $WORKDIR"
