CORES ?= 4
SNAKEFILE = workflow/Snakefile

.PHONY: run dryrun docker dag clean help

## One-click run (auto-detect environment)
run:
	bash run.sh --cores $(CORES)

## Dry-run (show what would execute, no actual computation)
dryrun:
	bash run.sh --dry-run

## Run inside Docker (builds image if needed)
docker:
	docker-compose up --build md-pipeline

## Interactive Docker shell for debugging
shell:
	docker-compose run --rm md-shell

## Visualize the Snakemake DAG (requires graphviz)
dag:
	conda run -n mdenv snakemake --snakefile $(SNAKEFILE) --dag | dot -Tpng -o results/dag.png
	@echo "DAG saved to results/dag.png"

## Lint Python scripts
lint:
	conda run -n mdenv ruff check scripts/ analysis/

## Set up conda environment
env:
	conda env create -f environment.yml
	@echo "✅ Run: conda activate mdenv"

## Remove all intermediate work files (keeps inputs/ and results/)
clean:
	rm -rf work/
	@echo "Cleaned work/ directory."

## Remove everything including results
distclean: clean
	rm -rf results/
	@echo "Cleaned work/ and results/."

## Show this help
help:
	@grep -E '^##' Makefile | sed 's/## /  /'
	@echo ""
	@echo "Usage: make [target] [CORES=N]"
	@echo "  Default CORES=4. Example: make run CORES=8"
