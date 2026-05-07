#!/usr/bin/env bash
# Run gmx_MMPBSA binding free energy analysis.
# Input:  work/05_md/{md.tpr, md.xtc}, work/03_complex/topol.top
# Output: results/mmpbsa/
set -euo pipefail

MDDIR="work/05_md"
OUTDIR="results/mmpbsa"
mkdir -p "$OUTDIR"

# Detect ligand residue name from topology
LIG_RESNAME=$(grep -E "^[A-Z0-9]{2,4}\s+1$" work/03_complex/topol.top | tail -1 | awk '{print $1}')
if [[ -z "$LIG_RESNAME" ]]; then
    LIG_RESNAME="MOL"
    echo "[06] WARNING: Could not detect ligand resname, using '$LIG_RESNAME'"
else
    echo "[06] Ligand residue name: $LIG_RESNAME"
fi

# Read frame settings from config
STARTFRAME=$(python3 -c "import yaml; p=yaml.safe_load(open('config/params.yaml')); print(p['mmpbsa']['startframe'])")
ENDFRAME=$(python3 -c "import yaml; p=yaml.safe_load(open('config/params.yaml')); print(p['mmpbsa']['endframe'])")
INTERVAL=$(python3 -c "import yaml; p=yaml.safe_load(open('config/params.yaml')); print(p['mmpbsa']['interval'])")

echo "[06] Running gmx_MMPBSA: frames $STARTFRAME-$ENDFRAME (every $INTERVAL) …"

# Patch mmpbsa.in with config values
sed -e "s/startframe=.*/startframe=$STARTFRAME,/" \
    -e "s/endframe=.*/endframe=$ENDFRAME,/" \
    -e "s/interval=.*/interval=$INTERVAL,/" \
    config/mmpbsa.in > "$OUTDIR/mmpbsa_runtime.in"

# Create index for receptor and ligand
python3 scripts/06_make_mmpbsa_index.py \
    --tpr  "$MDDIR/md.tpr" \
    --resname "$LIG_RESNAME" \
    --output "$OUTDIR/index.ndx"

gmx_MMPBSA \
    -O \
    -i  "$OUTDIR/mmpbsa_runtime.in" \
    -cs "$MDDIR/md.tpr" \
    -ct "$MDDIR/md.xtc" \
    -ci "$OUTDIR/index.ndx" \
    -cp "work/03_complex/topol.top" \
    -cg 1 13 \
    -prefix "$OUTDIR/MMPBSA" \
    -nogui \
    2>&1 | tee "$OUTDIR/gmx_mmpbsa.log"

echo "[06] MM-PB/GBSA complete → $OUTDIR"
echo "[06] Key results:"
grep -A 20 "GENERALIZED BORN" "$OUTDIR/FINAL_RESULTS_MMPBSA.dat" 2>/dev/null || \
grep -A 10 "DELTA TOTAL" "$OUTDIR/FINAL_RESULTS_MMPBSA.dat" 2>/dev/null || \
echo "    Check $OUTDIR/FINAL_RESULTS_MMPBSA.dat for full results."
