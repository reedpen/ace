import os
from pathlib import Path

import matplotlib
import pytest

# Force headless operations for all tests
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["MPLBACKEND"] = "Agg"
matplotlib.use("Agg")


@pytest.fixture(scope="session")
def sample_recording_dir() -> Path:
    """Committed fixture root used by autodetect and slow e2e tests."""
    return Path(__file__).resolve().parent / "data" / "sample_recording"
