# Ephys Pipeline

The ephys pipeline loads electrophysiology data through **`EphysDataManager.create(...)`**, which selects a concrete backend (currently **Neuralynx** or **ONIX RHS2116** based on files in the ephys directory). It then supports artifact removal, filtering, spectral analysis, and phase computation. For supported formats and how to add another, see [Creating new data loaders](adding_data_loaders.md).

## Quick Start

### Prerequisites

1. Ensure your project directory has:
   - `experiments.csv` with experiment metadata
   - `analysis_parameters.csv` with pipeline parameters

### Command Line

```bash
# Run with explicit project path
python -m ace_neuro.pipelines.ephys --line-num 96 --project-path /my/project

# Run with explicit project and data paths
python -m ace_neuro.pipelines.ephys --line-num 96 --project-path /my/project --data-path /my/raw_data

# Run in headless mode
python -m ace_neuro.pipelines.ephys --line-num 96 --project-path /my/project --headless
```

### Python API

```python
from ace_neuro.pipelines.ephys import EphysPipeline

api = EphysPipeline()
api.run(
    line_num=96, 
    project_path="/my/project",
    data_path="/my/raw_data",
    channel_name='PFCLFPvsCBEEG'
)
```

## Pipeline Steps

1. **Channel Loading**: Imports a raw block via the selected `EphysDataManager` (Neo/Neuralynx `.nev`/`.ncs`, or RHS2116 `.raw` streams, depending on `can_handle`).
2. **Artifact Removal**: Optional removal of electrical artifacts (Neuralynx path; behavior may differ by backend).
3. **Filtering**: Bandpass, lowpass, or highpass filtering with configurable parameters
4. **Spectrogram**: Multi-taper spectral analysis with sliding windows
5. **Phase Analysis**: Hilbert transform phase computation for specified frequency bands
6. **Visualization**: Channel traces and spectrogram plotting

## Key Parameters in `analysis_parameters.csv`

| Parameter | Description | Example |
|-----------|-------------|---------|
| `channel_name` | Neuralynx channel to analyze | `PFCLFPvsCBEEG` |
| `filter_type` | Filter type (`bandpass`, `lowpass`, `highpass`) | `bandpass` |
| `filter_range` | Filter frequency range [low, high] | `[0.5, 4]` |
| `zero time (s)` | Reference time for alignment | `0` |
| `baseline period (min)` | Baseline duration | `10` |

## Data Organization

Raw data paths are specified in `experiments.csv` under the **`ephys directory`** column (resolved relative to `data_path`). The files present must match **one** registered `EphysDataManager` subclass — for example Neuralynx `Events.nev` + `.ncs` channels, or ONIX RHS2116 `rhs2116pair-*.raw` together with `start-time_*.csv` as implemented in code.