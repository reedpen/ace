# Examples & Workflows

ACE-neuro is designed to be flexible. Below are common usage patterns and demonstration scripts included in the repository.

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

## 4. Interactive Tutorials

For a hands-on experience, we provide a series of Jupyter notebooks that walk through the core features of ACE-neuro:

- **[Miniscope Processing](notebooks/miniscope_pipeline_tutorial.ipynb)**: End-to-end calcium imaging workflow.
- **[Ephys Processing](notebooks/ephys_pipeline_tutorial.ipynb)**: Signal filtering and spectral analysis.
- **[Multimodal Alignment](notebooks/multimodal_alignment_tutorial.ipynb)**: Synchronizing independent datasets.

> [!TIP]
> **Check out the docstrings!** Every public method in ACE-neuro is documented with Google-style docstrings. Use `help(MiniscopePipeline)` in a Python REPL or check the [API Reference](../api/index.md) for detailed argument descriptions.
