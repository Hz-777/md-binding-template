#!/usr/bin/env bash
# One-click entry point for the MD + binding free energy pipeline.
# Detects the runtime environment and launches Snakemake accordingly.
set -euo pipefail

CORES="${CORES:-4}"
SNAKEFILE="workflow/Snakefile"

echo "================================================="
echo "  MD Binding Free Energy Pipeline"
echo "  $(date)"
echo "================================================="

# --- Preflight checks ---
if [[ ! -f "inputs/protein.pdb" ]]; then
    echo "ERROR: inputs/protein.pdb not found."
    echo "  Place your protein structure (PDB format) in inputs/"
    exit 1
fi
if [[ ! -f "inputs/ligand.sdf" ]]; then
    echo "ERROR: inputs/ligand.sdf not found."
    echo "  Place your ligand structure (SDF or MOL2 format) in inputs/"
    exit 1
fi

echo "[run] Protein:  inputs/protein.pdb"
echo "[run] Ligand:   inputs/ligand.sdf"
echo "[run] Config:   config/params.yaml"
echo "[run] Cores:    $CORES"
echo ""

# --- Detect environment ---
if command -v conda &>/dev/null && conda info --envs | grep -q "mdenv"; then
    echo "[run] Using conda environment 'mdenv'"
    RUNNER="conda run -n mdenv"
elif [[ -n "${CONDA_DEFAULT_ENV:-}" && "$CONDA_DEFAULT_ENV" == "mdenv" ]]; then
    echo "[run] Already in conda environment 'mdenv'"
    RUNNER=""
elif [[ -f "/opt/conda/envs/mdenv/bin/snakemake" ]]; then
    echo "[run] Using Docker/Codespaces conda environment"
    RUNNER="/opt/conda/envs/mdenv/bin"
    export PATH="$RUNNER:$PATH"
    RUNNER=""
else
    echo "WARNING: 'mdenv' conda environment not found."
    echo "  Run:  conda env create -f environment.yml"
    echo "  Then: conda activate mdenv && ./run.sh"
    echo ""
    echo "  Or use Docker:  docker-compose up"
    exit 1
fi

mkdir -p work/logs results

# --- Run Snakemake ---
echo "[run] Starting Snakemake workflow …"
echo ""

$RUNNER snakemake \
    --snakefile "$SNAKEFILE" \
    --cores "$CORES" \
    --rerun-incomplete \
    --printshellcmds \
    --reason \
    "$@"   # pass any extra args (e.g. --dry-run)

echo ""
echo "================================================="
echo "  Pipeline complete!"
echo "  Results:   results/"
echo "  Report:    results/report.html"
echo "  ΔG binding: $(grep 'DELTA G binding' results/mmpbsa/FINAL_RESULTS_MMPBSA.dat 2>/dev/null | head -1 || echo 'see results/mmpbsa/')"
echo "================================================="
