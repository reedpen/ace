# Multimodal Pipeline

The multimodal pipeline runs the **ephys** and **miniscope** sub-pipelines, then aligns their time bases for phase-locked and event-aligned analysis. Alignment is implemented through **`MiniscopeDataManager.sync_timestamps`** (which calls into **`EphysDataManager.get_sync_timestamps`** when TTL-based sync is used), not by hard-coding a single vendor.

## Quick Start

### Prerequisites

1. Ensure your project directory has:
   - `experiments.csv` with both **calcium imaging directory** and **ephys directory**
   - `analysis_parameters.csv` with parameters for both modalities

2. Ensure the **correct data managers** are selected for those directories (see [Creating new data loaders](adding_data_loaders.md#built-in-loaders-shipped-with-ace-neuro)). Typical lab setups:
   - **Neuralynx + UCLA Miniscope V3:** TTL pulses on an ephys channel + CSV/JSON miniscope metadata.
   - **ONIX RHS2116 + UCLA Miniscope V4:** hardware clock `.raw` streams; sync may rely on clock alignment rather than TTL extraction — your `sync_timestamps` / `get_sync_timestamps` implementations must reflect that.

### Command Line

```bash
# Run with explicit project path
python -m ace_neuro.pipelines.multimodal --line-num 97 --project-path /my/project

# Run with explicit project and data paths
python -m ace_neuro.pipelines.multimodal --line-num 97 --project-path /my/project --data-path /my/raw_data

# Run in headless mode
python -m ace_neuro.pipelines.multimodal --line-num 97 --project-path /my/project --headless
```

### Python API

```python
from ace_neuro.pipelines.multimodal import MultimodalPipeline

api = MultimodalPipeline()
api.run(
    line_num=97, 
    project_path="/my/project",
    data_path="/my/raw_data",
    headless=True
)
```

## Pipeline Steps

1. **Ephys sub-pipeline**: Loads channels via `EphysDataManager.create(...)` (Neuralynx or RHS2116, depending on files in **`ephys directory`**).
2. **Miniscope sub-pipeline**: Loads movies and metadata via `MiniscopeDataManager.create(...)` (UCLA V3 or ONIX V4, depending on files in **`calcium imaging directory`**).
3. **Timestamp synchronization**: Calls `sync_neuralynx_miniscope_timestamps`, which delegates to **`miniscope_dm.sync_timestamps(ephys_dm=...)`**. Neuralynx-specific cleanup of event lists runs only when the ephys manager is **`NeuralynxDataManager`**.
4. **TTL / frame mapping**: Maps aligned calcium times to ephys sample indices where TTL-based framing applies.
5. **Phase-based event analysis** (optional): Computes calcium event phases relative to ephys oscillations when event indices are available.
6. **Phase histograms**: Circular histograms of event-phase distributions when phases are computed.

## Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `delete_TTLs` | Remove problematic TTL events | `True` |
| `fix_TTL_gaps` | Correct gaps in TTL timing | `False` in `MultimodalPipeline.run` (CLI defaults may differ — see `python -m ace_neuro.pipelines.multimodal` defaults) |
| `only_experiment_events` | Restrict to experimental time window | `True` |
| `all_TTL_events` | Use all detected TTL events | `True` |
| `ca_events` | Analyze calcium events | `False` in API default; CLI template sets `True` |
| `time_range` | Time window to analyze (seconds) | `None` |

All ephys and miniscope parameters from their respective pipelines also apply here.

## Data Requirements

The `experiments.csv` row must include:

- **`calcium imaging directory`**: Path to miniscope recordings (resolved relative to `data_path`).
- **`ephys directory`**: Path to ephys recordings (resolved relative to `data_path`).

Those directories should contain **one coherent acquisition** from the same session. The expected **file types** depend on which built-in (or custom) loaders match; they are not limited to “Neuralynx folders only” or “UCLA V3 only.” If multimodal alignment fails, verify TTL availability, `sync_timestamps` behavior for your pair of loaders, and [Creating new data loaders](adding_data_loaders.md).
