#!/usr/bin/env bash
# Copy tutorial notebooks from repo root into docs/ for MkDocs (mkdocs-jupyter).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "${ROOT}/docs/notebooks"
cp "${ROOT}/notebooks"/*.ipynb "${ROOT}/docs/notebooks/"
