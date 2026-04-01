#!/usr/bin/env bash
# Copy tutorial notebooks from notebooks/ into docs/notebooks/ for mkdocs-jupyter.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${ROOT}/notebooks"
DST="${ROOT}/docs/notebooks"
mkdir -p "${DST}"
cp -f "${SRC}"/*.ipynb "${DST}/"
echo "Synced notebooks: ${SRC} -> ${DST}"
