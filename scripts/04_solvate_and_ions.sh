#!/usr/bin/env bash
# Solvate the complex and add counterions.
# Input:  work/03_complex/{complex.gro, topol.top, index.ndx}
# Output: work/04_solvated/{solvated_ions.gro, topol.top (updated)}
set -euo pipefail

SRC="work/03_complex"
WORKDIR="work/04_solvated"
mkdir -p "$WORKDIR"

cp "$SRC/topol.top" "$WORKDIR/topol.top"
cp "$SRC/index.ndx" "$WORKDIR/index.ndx"

echo "[04] Defining simulation box (dodecahedron, 1.2 nm padding) …"
gmx editconf \
    -f "$SRC/complex.gro" \
    -o "$WORKDIR/complex_box.gro" \
    -c \
    -d 1.2 \
    -bt dodecahedron \
    -quiet

echo "[04] Solvating with TIP3P water …"
gmx solvate \
    -cp "$WORKDIR/complex_box.gro" \
    -cs spc216.gro \
    -o "$WORKDIR/solvated.gro" \
    -p "$WORKDIR/topol.top" \
    -quiet

echo "[04] Adding NaCl ions to 0.15 mol/L …"
gmx grompp \
    -f config/em.mdp \
    -c "$WORKDIR/solvated.gro" \
    -p "$WORKDIR/topol.top" \
    -o "$WORKDIR/ions.tpr" \
    -maxwarn 2 \
    -quiet

# Select SOL group (usually group 13) for ion replacement
echo "SOL" | gmx genion \
    -s "$WORKDIR/ions.tpr" \
    -o "$WORKDIR/solvated_ions.gro" \
    -p "$WORKDIR/topol.top" \
    -pname NA \
    -nname CL \
    -neutral \
    -conc 0.15 \
    -quiet

echo "[04] Solvation complete → $WORKDIR/solvated_ions.gro"
