# Getting Started with ACE-neuro

Welcome to the Experiment Analysis pipeline! This guide will help you set up your environment, organize your data, and run your first analysis.

> **Note:** Section numbers were revised for clarity. Content that used to appear under “3a” (passing parameters into pipelines) is now **section 5a**.

---

## 1. Prerequisites

* **Python 3.10+** — `pyproject.toml` allows 3.10–3.12. The provided **conda** environment pins **Python 3.10** to match CaImAn and CI expectations.
* **Conda or Mamba** — Recommended for installing CaImAn and scientific stack binaries (OpenCV, etc.).
* **CaImAn** — Required for the Miniscope (calcium imaging) pipeline. It is not reliably installed from PyPI alone; use **conda-forge** (see below).

---

## 2. Platform support and what “works out of the box”

| Environment | Status | Notes |
|-------------|--------|--------|
| **Linux x86_64** | **Primary target** | Used for development and automated tests (`pytest`). The supported conda recipe is `linux_environment.yml`. |
| **macOS** | **Best-effort** | Conda-forge builds exist for CaImAn and dependencies; interactive GUIs (Tkinter, Qt) may need extra system configuration. Not exercised in CI on every commit. |
| **Windows** | **Best-effort** | Same as macOS: conda-forge is the practical path. Path handling in the code uses `pathlib`; use consistent drive/UNC paths in `experiments.csv`. |

**Read the Docs** builds the documentation site on **Ubuntu** with Python 3.11 and installs the package **without CaImAn** (`pip install --no-deps -e .` in `.readthedocs.yaml`) so API pages render without a full imaging stack. That is **not** a substitute for a local analysis environment when you run pipelines.

**Avoid** using the committed `environment.yml` at the repository root for new installs: it is a **machine-specific, fully pinned export** (it even contains a foreign `prefix:`). For reproducible setups, use **`linux_environment.yml`** (minimal, cross-machine) and let conda resolve versions, or create and export your own environment after you have a working stack.

---

## 3. Installation

Clone the repository and install the package in editable mode.

### Recommended: conda environment + editable install

This matches the [repository README installation section](https://github.com/emelon8/experiment_analysis/blob/main/README.md#installation) and avoids `pip` trying to pull CaImAn from PyPI while conda already provides it:

```bash
git clone https://github.com/emelon8/experiment_analysis.git
cd experiment_analysis

# conda works too; mamba is faster at solving
mamba env create -f linux_environment.yml
conda activate caiman

# Install the ace-neuro package without re-resolving heavy deps already in the env
pip install -e . --no-deps
```

Optional: **`pip install -e ".[box]"`** (or `pip install -e ".[all]"`) if you use Box-backed downloads (`ace_neuro.shared.file_downloader`).

### Alternative: pip-only (advanced)

If you already have **CaImAn** and scientific dependencies installed (for example from conda-forge into a virtualenv), you can run `pip install -e .` and let `pyproject.toml` pull runtime dependencies. You are then responsible for a working CaImAn/OpenCV stack on your OS.

---

## 4. How the codebase is meant to extend

ACE-neuro is built around **explicit paths** (`project_path`, `data_path`), **CSV-driven metadata** (`experiments.csv`, `analysis_parameters.csv`), and **pluggable data managers**:

- **`ExperimentDataManager`** loads cohort metadata and analysis parameters.
- **`MiniscopeDataManager`** / **`EphysDataManager`** abstract raw acquisition formats. Subclasses register automatically; **`create(...)`** picks the first subclass whose **`can_handle(directory)`** is true.

For new file layouts or hardware, you add a subclass and ensure it is imported before pipelines run. See **[Creating new data loaders](guides/adding_data_loaders.md)** for methods, registration, registry order, and multimodal sync expectations.

High-level pipelines (`MiniscopePipeline`, `EphysPipeline`, `MultimodalPipeline`) orchestrate processing without hard-coding a single vendor format—as long as the right manager is registered.

---

## 5. Data Organization

The pipeline relies on a structured project directory. Each project should contain:

### A. Project Repository (`project_path`)
This directory holds your configuration files:
- `experiments.csv`: Master list of every experiment/recording session.
- `analysis_parameters.csv`: Parameter overrides (cropping, filtering, etc.) for specific experiments.

### B. Shared Data Storage (`data_path`)
This is where your raw experimental data lives:
- **Miniscope Data**: e.g. `.avi` movies, UCLA V3 `metaData*.json` / `timeStamps*.csv`, or UCLA V4 ONIX-style `start-time_*_miniscope.csv` and clock `.raw` files (see [Creating new data loaders](guides/adding_data_loaders.md#built-in-loaders-shipped-with-ace-neuro)).
- **Ephys Data**: e.g. Neuralynx `.nev` / `.ncs`, or ONIX RHS2116 `.raw` streams — again determined by the concrete `EphysDataManager` subclass.

Path fields inside `experiments.csv` (for example **ephys directory** and **calcium imaging directory**) are resolved **relative to `data_path`**, not inside `project_path`.

To support a new on-disk recording format (new filenames, metadata, or sync rules), implement a custom loader as described in [Creating new data loaders](guides/adding_data_loaders.md).

---

## 5a. Passing parameters into the pipelines (read this)

Every pipeline is driven by **keyword arguments** to `run()`. There are three ways those kwargs get set; they stack in this order (later steps override earlier ones):

| Source | What it sets | When to use |
|--------|----------------|-------------|
| **1. Defaults in code** | Built-in defaults inside `EphysPipeline.run`, `MiniscopePipeline.run`, `MultimodalPipeline.run` | Starting point; see [API — Pipelines](api/pipelines.md) or `help(EphysPipeline.run)` in Python. |
| **`analysis_parameters.csv`** | Per–line-number overrides for the same kwarg names (via `load_analysis_params`) | Reproducible, shareable settings per experiment row. Column names match kwargs where possible (see `ace_neuro.shared.config_utils.parse_analysis_params`). |
| **Your call** | Explicit arguments to `run(...)` or a dict you merge yourself | Final say: pass any kwarg the pipeline accepts. |

**Always required (for real data):**

- `line_num` — row in `experiments.csv` / `analysis_parameters.csv`
- `project_path` — directory containing those CSVs
- `data_path` — raw data root (strongly recommended; if omitted, the library may fall back to a path under the repo)

**Python — pass kwargs directly**

```python
from pathlib import Path
from ace_neuro.pipelines.miniscope import MiniscopePipeline

api = MiniscopePipeline()
api.run(
    line_num=96,
    project_path=Path("/path/to/project"),
    data_path=Path("/path/to/raw_data"),
    filenames=["0.avi"],
    run_CNMFE=True,
    headless=True,
)
```

**Python — merge CSV row, then override**

```python
from ace_neuro.shared.config_utils import load_analysis_params
from ace_neuro.pipelines.ephys import EphysPipeline

project = Path("/path/to/project")
params = load_analysis_params(96, project_path=project)
params.update(
    project_path=project,
    data_path=Path("/path/to/raw_data"),
    headless=True,
    filter_type="butter",
    filter_range=[0.5, 4.0],
)
EphysPipeline().run(**params)
```

`load_analysis_params` returns only keys present in your CSV; empty cells are skipped so pipeline defaults still apply.

**Command line — only a few flags; the rest comes from defaults + CSV**

The `python -m ace_neuro.pipelines.*` entry points accept **`--line-num`**, **`--project-path`**, optional **`--data-path`**, and usually **`--headless`**. They build a `run_params` dict (defaults), then **`run_params.update(load_analysis_params(...))`**, then apply CLI path/headless overrides. You **cannot** set arbitrary kwargs (e.g. `filter_range`) from the CLI unless you add flags or use the Python API / CSV.

**Where to see every parameter**

- Docstrings: `help(MiniscopePipeline.run)` (same pattern for ephys and multimodal).
- [API Reference — Pipelines](api/pipelines.md).

---

## 5b. Tutorials (Jupyter + documentation site)

Step-by-step notebooks stress-test this layout: they **assert both CSVs exist** under `project_path` before any pipeline runs.

| Topic | In the docs site | Notebook source in repo |
|-------|------------------|-------------------------|
| Miniscope | [Tutorial](https://ace-neuro.readthedocs.io/en/latest/notebooks/miniscope_pipeline_tutorial/) | `notebooks/miniscope_pipeline_tutorial.ipynb` |
| Ephys | [Tutorial](https://ace-neuro.readthedocs.io/en/latest/notebooks/ephys_pipeline_tutorial/) | `notebooks/ephys_pipeline_tutorial.ipynb` |
| Multimodal | [Tutorial](https://ace-neuro.readthedocs.io/en/latest/notebooks/multimodal_alignment_tutorial/) | `notebooks/multimodal_alignment_tutorial.ipynb` |

---

## 6. Configuring paths (still explicit)

Paths are **`project_path`** and **`data_path`** — there are no hidden environment variables or `.env` files. See **section 5a** for how paths combine with other parameters.

### Option 1: Command line (scripts and HPC)

Only path-related flags plus `headless`; other behavior comes from **defaults + `analysis_parameters.csv`** (see section 5a).

```bash
python -m ace_neuro.pipelines.miniscope \
  --line-num 96 \
  --project-path /path/to/your/project \
  --data-path /path/to/your/raw_data \
  --headless
```

### Option 2: Programmatic API (notebooks and scripts)

Pass **all** kwargs to `run()` — see section 5a for the full pattern.

```python
from ace_neuro.pipelines.miniscope import MiniscopePipeline

api = MiniscopePipeline()
api.run(
    line_num=96,
    project_path="/path/to/project",
    data_path="/path/to/data",
)
```

> **Note:** If `data_path` is omitted, it may default to a path under the repository; always pass it explicitly for real experiments.

---

## 7. Running Your First Pipeline

### Miniscope Analysis
Executes preprocessing, motion correction, source extraction (CNMF-E), and post-processing.
```bash
python -m ace_neuro.pipelines.miniscope --line-num 96 --project-path /path/to/project
```

### Ephys Analysis
Loads ephys channels, filters signals, and generates spectrograms.
```bash
python -m ace_neuro.pipelines.ephys --line-num 96 --project-path /path/to/project
```

### Multimodal (Synchronized) Analysis
Aligns miniscope and ephys time bases and performs synchronized analysis (TTL-based for typical Neuralynx + UCLA V3 setups; hardware-clock paths for some ONIX configurations — see [Multimodal guide](guides/multimodal.md)).
```bash
python -m ace_neuro.pipelines.multimodal --line-num 97 --project-path /path/to/project
```

---

## 8. Resources and Documentation
- **Docs home**: [index.md](index.md) (includes tutorial links).
- **Examples**: [examples.md](examples.md).
- **Data management (CSVs, paths)**: [guides/data_management.md](guides/data_management.md).
- **Creating data loaders**: [guides/adding_data_loaders.md](guides/adding_data_loaders.md) — extend miniscope and ephys loaders for new recording formats.
- **Box integration**: `ace_neuro/shared/file_downloader.py` for automated retrieval when credentials are configured.
