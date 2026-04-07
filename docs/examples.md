# Examples & Workflows

ACE-neuro is designed to be flexible. Below are common usage patterns and demonstration scripts included in the repository.

**Passing parameters:** pipeline behavior is controlled by **kwargs to `run()`**, optional rows in **`analysis_parameters.csv`**, and (for CLI) built-in defaults merged with that CSV. Read **section 5a** in [Getting started](getting_started.md) before copying snippets below.

## 1. Explicit Paths API
**Script**: `examples/explicit_paths_demo.py`

This script demonstrates the "explicit path" philosophy of ACE-neuro. It shows how to initialize and run each of the three main pipelines without relying on any environment variables or hidden configuration files.

```python
from ace_neuro.pipelines.miniscope import MiniscopePipeline

# Run with explicit project and data paths
api = MiniscopePipeline()
api.run(
    line_num=96,
    project_path="/path/to/project",
    data_path="/path/to/raw_data"
)
```

## 2. Supercomputer (Slurm) Workflow
**Script**: `submit_job.slurm`

For high-throughput processing, ACE-neuro includes a standard Slurm submission script. It handles the resource allocation (150GB RAM, multiple cores) and executes the pipelines in `headless` mode.

```bash
# Submit the job to your cluster
sbatch submit_job.slurm
```

## 3. Data Integration Workflows

### Batch Processing
Since ACE-neuro is driven by an `experiments.csv` file, you can easily wrap it in a simple Python loop or bash script to process hundreds of recording sessions with a single command.

### Cloud Integration
The pipeline uses `ace_neuro/shared/file_downloader.py` to check for data locally. If missing, and if `box_credentials.py` is configured, it will automatically pull the required binary data from Box.

### Custom acquisition formats
If your recordings are not recognized by the built-in loaders, add a `MiniscopeDataManager` or `EphysDataManager` subclass and register it (see [Creating new data loaders](guides/adding_data_loaders.md)). The same CSV layout and pipelines apply once the correct loader is selected.

## 4. Interactive Tutorials

Notebooks emphasize **`project_path`** (CSVs) vs **`data_path`** (raw data) before running pipelines. They render on the docs site via **mkdocs-jupyter** ([Miniscope](https://ace-neuro.readthedocs.io/en/latest/notebooks/miniscope_pipeline_tutorial/), [Ephys](https://ace-neuro.readthedocs.io/en/latest/notebooks/ephys_pipeline_tutorial/), [Multimodal](https://ace-neuro.readthedocs.io/en/latest/notebooks/multimodal_alignment_tutorial/)).

| Notebook | In-repo after `scripts/sync_notebooks_for_docs.sh` |
|----------|-----------------------------------------------------|
| Miniscope | [notebooks/miniscope_pipeline_tutorial.ipynb](notebooks/miniscope_pipeline_tutorial.ipynb) |
| Ephys | [notebooks/ephys_pipeline_tutorial.ipynb](notebooks/ephys_pipeline_tutorial.ipynb) |
| Multimodal | [notebooks/multimodal_alignment_tutorial.ipynb](notebooks/multimodal_alignment_tutorial.ipynb) |

> [!TIP]
> **Docstrings:** use `help(MiniscopePipeline)` or the [API Reference](api/index.md).
