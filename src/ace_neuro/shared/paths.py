"""
Path configuration for the experiment_analysis package.

All data paths (project_path, data_path) must be provided explicitly by the
user — either as arguments to Pipeline/DataManager constructors, or as CLI
flags (--project-path, --data-path).

There is no hidden state: no .env files, no environment variable lookups.
"""

from pathlib import Path

# Package root (experiment_analysis/)
PROJECT_ROOT: Path = Path(__file__).parent.parent.parent

# Legacy alias kept for Box credentials and internal data directory
DATA_DIR: Path = PROJECT_ROOT / "data"