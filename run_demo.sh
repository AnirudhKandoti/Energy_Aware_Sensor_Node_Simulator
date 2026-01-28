#!/usr/bin/env bash
set -e
python main.py --policy adaptive --out results_adaptive
python main.py --policy fixed --out results_fixed
python main.py --policy duty --out results_duty
echo "Done. Check the results_* folders."
