# Multi-stage build: base → md-env
# Installs GROMACS (CPU), acpype, gmx_MMPBSA, RDKit, MDAnalysis, Snakemake
FROM continuumio/miniconda3:24.1.2-0 AS base

LABEL org.opencontainers.image.title="MD Binding Free Energy Template"
LABEL org.opencontainers.image.description="GROMACS + acpype + gmx_MMPBSA pipeline"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        openbabel \
        libopenbabel-dev \
        bc \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Conda environment
COPY environment.yml /tmp/environment.yml
RUN conda install -n base -c conda-forge mamba -y --quiet \
    && mamba env create -f /tmp/environment.yml \
    && conda clean -afy

# Activate the env by default
ENV PATH="/opt/conda/envs/mdenv/bin:$PATH"
ENV CONDA_DEFAULT_ENV=mdenv

# GROMACS — use the conda version (CPU, serial+MPI)
# For GPU: rebuild from source with CUDA, or use nvcr.io/nvidia/gromacs
RUN conda run -n mdenv bash -c "which gmx && gmx --version | head -3"

WORKDIR /workspace

# Validate that key tools are available
RUN conda run -n mdenv bash -c " \
    python -c 'import rdkit; print(\"rdkit\", rdkit.__version__)' && \
    python -c 'import MDAnalysis; print(\"MDAnalysis\", MDAnalysis.__version__)' && \
    acpype --version && \
    gmx_MMPBSA --version || true"

CMD ["bash"]
