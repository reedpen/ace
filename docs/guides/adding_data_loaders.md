# Creating New Data Loaders

This guide explains how to add support for a new recording format by implementing a new data manager class.

ACE-neuro selects data managers at runtime using factory methods:

- `MiniscopeDataManager.create(...)` for calcium imaging data
- `EphysDataManager.create(...)` for ephys data

Both factories iterate through registered subclasses and pick the first one whose `can_handle(...)` method returns `True`.

Related docs: [Data management (CSVs and paths)](data_management.md), [Getting started — platform support and installation](../getting_started.md#2-platform-support-and-what-works-out-of-the-box).

## Built-in loaders shipped with ACE-neuro

These are the classes you get **without writing code**, as long as the experiment row in `experiments.csv` points at a directory whose files match `can_handle`.

### Miniscope (`MiniscopeDataManager` subclasses)

| Class | Typical files / cues | Role |
|-------|----------------------|------|
| `OnixMiniscopeDataManager` | `start-time_*_miniscope.csv`, `ucla-miniscope-v4-clock_*.raw`, etc. | UCLA Miniscope **V4 / ONIX**-style hardware clock and metadata. |
| `UCLADataManager` | `metaData*.json`, `timeStamps*.csv`, `.avi` movies | UCLA Miniscope **V3** (JSON + CSV timestamps). |

**Order:** The factory tries subclasses in **registration order**. Registration order follows **import order** in `ace_neuro.pipelines.miniscope` (currently `OnixMiniscopeDataManager` is imported before `UCLADataManager`). The first class whose `can_handle(miniscope_directory)` is true wins. If both ONIX and V3 markers could match, tighten `can_handle` or split data into separate directories.

### Ephys (`EphysDataManager` subclasses)

| Class | Typical files / cues | Role |
|-------|----------------------|------|
| `RHS2116DataManager` | `rhs2116pair-*.raw`, `start-time_*.csv` (ephys, not miniscope) | **ONIX RHS2116** binary streams (intan-style layout used in this codebase). |
| `NeuralynxDataManager` | `Events.nev`, `.ncs` channel files | **Neuralynx** recordings via Neo. |

**Order:** Imports in `ace_neuro.pipelines.ephys` register **RHS2116 before Neuralynx**. `can_handle` for RHS matches broad `*.raw` patterns; use **distinct directories** per system so the correct loader is chosen.

### Experiment metadata (all pipelines)

`ExperimentDataManager` reads `experiments.csv` / `analysis_parameters.csv` and supplies paths such as **`calcium imaging directory`** and **`ephys directory`** (resolved relative to `data_path`). Custom columns flow into `metadata` for your loaders and scripts.

## How Discovery Works

Subclass registration is automatic through each base class' `__init_subclass__`, but your class still has to be imported so Python executes the class definition.

In practice, this means:

1. Define your subclass in `src/ace_neuro/miniscope/` or `src/ace_neuro/ephys/`.
2. Ensure it is imported by pipeline code before `create(...)` is called.
   - Miniscope imports currently happen in `ace_neuro.pipelines.miniscope`.
   - Ephys imports currently happen in `ace_neuro.pipelines.ephys`.

If your class is not imported, it will not be in the registry and the factory cannot choose it.

**Multimodal pipelines:** `MultimodalPipeline` calls `miniscope_dm.sync_timestamps(ephys_dm=..., ...)` after both single-modality pipelines run. Your `sync_timestamps` must agree with `ephys_dm.get_sync_timestamps` (TTL extraction vs hardware-clock alignment). The helper `sync_neuralynx_miniscope_timestamps` in code is a thin wrapper around `MiniscopeDataManager.sync_timestamps`; Neuralynx-specific event filtering applies only when the ephys manager is `NeuralynxDataManager`.

**Operating systems:** Use `pathlib.Path` and avoid hard-coded `/` vs `\\` in `can_handle`; the same loader code is intended to run on Linux, macOS, and Windows when dependencies are available.

---

## Add a New Miniscope Loader

Create a class that inherits from `MiniscopeDataManager` and implement all required abstract methods:

- `can_handle(cls, directory)`
- `_get_miniscope_metadata(self)`
- `_get_timestamps(self)`
- `_get_miniscope_events(self)`
- `sync_timestamps(self, ephys_dm=None, channel_name=None, **kwargs)`

Minimal skeleton:

```python
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from ace_neuro.miniscope.miniscope_data_manager import MiniscopeDataManager


class MyMiniscopeDataManager(MiniscopeDataManager):
    @classmethod
    def can_handle(cls, directory: Union[str, Path]) -> bool:
        directory = Path(directory)
        return directory.exists() and len(list(directory.rglob("my-format-marker.ext"))) > 0

    def _get_miniscope_metadata(self) -> Dict[str, Any]:
        # Parse files and return metadata. Must include frameRate when possible.
        return {"frameRate": 30.0}

    def _get_timestamps(self) -> Tuple[np.ndarray, List[int]]:
        # Return timestamps in seconds and frame numbers.
        t = np.arange(0, 10, 1 / 30.0)
        frame_numbers = list(range(len(t)))
        return t, frame_numbers

    def _get_miniscope_events(self) -> Dict[str, Any]:
        # Expected shape: {"timestamps": [...], "labels": [...]}
        return {"timestamps": [], "labels": []}

    def sync_timestamps(
        self,
        ephys_dm: Optional[Any] = None,
        channel_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Tuple[np.ndarray, np.ndarray]:
        # Return aligned calcium times and low-confidence periods.
        low_confidence = np.empty((0, 2))
        if self.time_stamps is None:
            raise ValueError("time_stamps not loaded")
        return self.time_stamps, low_confidence
```

### Miniscope Notes

- `MiniscopeDataManager.__init__` loads movie paths and calls `load_attributes(...)` when `auto_import_data=True`.
- `load_attributes(...)` expects `_get_timestamps`, `_get_miniscope_metadata`, and `_get_miniscope_events` to work together.
- `sync_timestamps(...)` should return:
  - `tCaIm`: aligned calcium timestamps
  - `low_confidence_periods`: `N x 2` index ranges where timing confidence is reduced (empty array if none)

---

## Add a New Ephys Loader

Create a class that inherits from `EphysDataManager` and implement:

- `can_handle(cls, directory)`
- `import_ephys_block(self, ephys_directory)`
- `process_ephys_block_to_channels(self, channels=None, remove_artifacts=False)`
- `get_sync_timestamps(self, channel_name=None)`

Minimal skeleton:

```python
from pathlib import Path
from typing import List, Optional, Union
import numpy as np
from ace_neuro.ephys.ephys_data_manager import EphysDataManager
from ace_neuro.ephys.channel import Channel


class MyEphysDataManager(EphysDataManager):
    @classmethod
    def can_handle(cls, directory: Union[str, Path]) -> bool:
        directory = Path(directory)
        return directory.exists() and len(list(directory.glob("*.mybin"))) > 0

    def import_ephys_block(self, ephys_directory: Union[str, Path]) -> None:
        # Load raw source data into self.ephys_block.
        self.ephys_block = {"path": str(ephys_directory)}

    def process_ephys_block_to_channels(
        self, channels: Optional[List[str]] = None, remove_artifacts: bool = False
    ) -> None:
        # Convert raw block into Channel objects and store in self.channels.
        sampling_rate = 1000.0
        t = np.arange(0, 10, 1 / sampling_rate)
        signal = np.zeros_like(t)
        self.channels["MY_CH_0"] = Channel("MY_CH_0", signal, sampling_rate, t, {"labels": [], "timestamps": []})

    def get_sync_timestamps(self, channel_name: Optional[str] = None) -> np.ndarray:
        # Return hardware sync event times in seconds.
        return np.array([])
```

### Ephys Notes

- `process_ephys_block_to_channels(...)` should populate `self.channels` with `Channel` instances expected by downstream filtering and visualization code. Each `Channel` needs a sensible `sampling_rate`, `time_vector`, and optional `events` dict for TTL-like labels when applicable.
- `get_sync_timestamps(...)` is used by multimodal alignment (via `miniscope_dm.sync_timestamps(..., ephys_dm=...)`). Return rising-edge sync times in **seconds**. Return an **empty** array only when sync pulses do not exist because timing is already shared (for example, some ONIX paths where the miniscope loader returns hardware-aligned frame times and TTL alignment is unnecessary).

---

## End-to-end checklist (smooth downstream)

1. **CSV**: Add or verify rows in `experiments.csv` so `calcium imaging directory` / `ephys directory` resolve under `data_path`.
2. **Loader**: Implement `can_handle` + required abstract methods; match **built-in** patterns if you extend an existing family.
3. **Register**: Import your module from `ace_neuro.pipelines.miniscope` or `ace_neuro.pipelines.ephys` (or another entry point that runs before `create`).
4. **Smoke test**: `MiniscopeDataManager.create(line_num=..., project_path=..., data_path=...)` or `EphysDataManager.create(ephys_directory=...)` and print `type(...)`.
5. **Single-modality pipeline**: Run `MiniscopePipeline` or `EphysPipeline` on a real line number.
6. **Multimodal (if needed)**: Confirm `sync_timestamps` and `get_sync_timestamps` implement a consistent time base; run `MultimodalPipeline` with representative kwargs.

---

## Choosing `can_handle(...)` Safely

`can_handle(...)` methods should be:

- Specific enough to avoid false positives when multiple formats are present
- Fast (check for marker files, not full parsing)
- Stable across sessions and recordings

Use explicit signatures like well-known filenames or extensions (for example, `Events.nev`, `start-time_*_miniscope.csv`, `rhs2116pair-ac_*.raw`).

Quick factory check:

```python
from ace_neuro.miniscope.miniscope_data_manager import MiniscopeDataManager
# or: from ace_neuro.ephys.ephys_data_manager import EphysDataManager

dm = MiniscopeDataManager.create(line_num=1, project_path="/path/to/project", data_path="/path/to/raw_data")
print(type(dm))
```

---

## Testing Recommendations

- Add a fixture directory in `tests/data/` with a minimal sample of the new format.
- Add a factory test that asserts `create(...)` resolves to your subclass.
- Add one behavior test for each critical parser:
  - metadata parsing
  - timestamp extraction
  - channel/event extraction
- For multimodal use, add a sync timestamp test to validate alignment assumptions.

With these pieces in place, the new loader should work transparently in existing pipelines.
