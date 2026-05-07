#!/usr/bin/env bash
# Run energy minimization → NVT → NPT → Production MD
# Reads GPU setting from config/params.yaml
set -euo pipefail

SRC="work/04_solvated"
WORKDIR="work/05_md"
mkdir -p "$WORKDIR"

# Parse GPU flag
GPU_ENABLED=$(python3 -c "
import yaml
p = yaml.safe_load(open('config/params.yaml'))
print('1' if p.get('gpu',{}).get('enabled', False) else '0')
")
GPU_ARGS=""
if [[ "$GPU_ENABLED" == "1" ]]; then
    GPU_ID=$(python3 -c "import yaml; p=yaml.safe_load(open('config/params.yaml')); print(p['gpu']['gpu_id'])")
    GPU_ARGS="-gpu_id $GPU_ID -ntmpi 1 -ntomp 8"
    echo "[05] GPU mode: gpu_id=$GPU_ID"
else
    echo "[05] CPU mode"
fi

cp "$SRC/topol.top" "$WORKDIR/topol.top"
cp "$SRC/index.ndx" "$WORKDIR/index.ndx"

# ---------- Energy Minimization ----------
echo "[05] EM: energy minimization …"
gmx grompp \
    -f config/em.mdp \
    -c "$SRC/solvated_ions.gro" \
    -p "$WORKDIR/topol.top" \
    -o "$WORKDIR/em.tpr" \
    -maxwarn 2 -quiet

gmx mdrun \
    -v \
    -deffnm "$WORKDIR/em" \
    $GPU_ARGS \
    2>&1 | tee "$WORKDIR/em.log"

echo "[05] EM done. Final potential energy:"
echo "0" | gmx energy -f "$WORKDIR/em.edr" -o "$WORKDIR/em_potential.xvg" -quiet 2>/dev/null || true

# ---------- NVT Equilibration ----------
echo "[05] NVT equilibration (200 ps) …"
gmx grompp \
    -f config/nvt.mdp \
    -c "$WORKDIR/em.gro" \
    -r "$WORKDIR/em.gro" \
    -p "$WORKDIR/topol.top" \
    -n "$WORKDIR/index.ndx" \
    -o "$WORKDIR/nvt.tpr" \
    -maxwarn 2 -quiet

gmx mdrun \
    -v \
    -deffnm "$WORKDIR/nvt" \
    $GPU_ARGS \
    2>&1 | tee "$WORKDIR/nvt.log"

# ---------- NPT Equilibration ----------
echo "[05] NPT equilibration (200 ps) …"
gmx grompp \
    -f config/npt.mdp \
    -c "$WORKDIR/nvt.gro" \
    -r "$WORKDIR/nvt.gro" \
    -t "$WORKDIR/nvt.cpt" \
    -p "$WORKDIR/topol.top" \
    -n "$WORKDIR/index.ndx" \
    -o "$WORKDIR/npt.tpr" \
    -maxwarn 2 -quiet

gmx mdrun \
    -v \
    -deffnm "$WORKDIR/npt" \
    $GPU_ARGS \
    2>&1 | tee "$WORKDIR/npt.log"

# ---------- Production MD ----------
PROD_STEPS=$(python3 -c "import yaml; p=yaml.safe_load(open('config/params.yaml')); print(p['md']['prod_steps'])")
echo "[05] Production MD ($PROD_STEPS steps = $(echo "$PROD_STEPS * 0.002 / 1000" | bc -l | xargs printf '%.1f') ns) …"

# Patch prod_steps into md.mdp
sed "s/^nsteps.*/nsteps = $PROD_STEPS/" config/md.mdp > "$WORKDIR/md_runtime.mdp"

gmx grompp \
    -f "$WORKDIR/md_runtime.mdp" \
    -c "$WORKDIR/npt.gro" \
    -t "$WORKDIR/npt.cpt" \
    -p "$WORKDIR/topol.top" \
    -n "$WORKDIR/index.ndx" \
    -o "$WORKDIR/md.tpr" \
    -maxwarn 2 -quiet

gmx mdrun \
    -v \
    -deffnm "$WORKDIR/md" \
    $GPU_ARGS \
    2>&1 | tee "$WORKDIR/md.log"

echo "[05] All MD stages complete → $WORKDIR"
echo "[05] Trajectory: $WORKDIR/md.xtc"
