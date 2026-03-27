from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pytest

from ace_neuro.miniscope.ucla_data_manager import UCLADataManager
from ace_neuro.pipelines.miniscope import MiniscopePipeline

# Define paths for our mock dataset (miniscope-only; ephys is not exercised here)
TEST_DATA_DIR = Path(__file__).parent / "data" / "sample_recording"
MINISCOPE_DIR = TEST_DATA_DIR / "UCLA and Neuralynx" / "miniscope"

MOCK_ANALYSIS_PARAMS: dict[str, Any] = {
    "crop": False,
    "detrend_method": "median",
    "df_over_f": True,
    "secs_window": 5,
    "quantile_min": 8,
    "df_over_f_method": "delta_f_over_sqrt_f",
    "parallel": False,
    "n_processes": 1,
    "apply_motion_correction": False,
    "inspect_motion_correction": False,
    "plot_params": False,
    "run_CNMFE": True,
    "save_estimates": True,
    "save_CNMFE_estimates_filename": "test_estimates.hdf5",
    "save_CNMFE_params": False,
    "remove_components_with_gui": False,
    "find_calcium_events": True,
    "derivative_for_estimates": "first",
    "event_height": 5,
    "compute_miniscope_phase": False,
    "filter_miniscope_data": False,
    "compute_miniscope_spectrogram": False,
    "headless": True,
}


@pytest.mark.slow
class TestEndToEndPipeline:
    @pytest.fixture
    def mock_data_exists(self):
        """Skip if committed miniscope fixtures are missing (clone without test data)."""
        if not MINISCOPE_DIR.is_dir():
            pytest.skip(
                "Miniscope fixture directory missing: tests/data/sample_recording/.../miniscope. "
                "Restore from the repository or run scripts/create_test_data.py if you have sample data."
            )

        avi_files = list(MINISCOPE_DIR.glob("*.avi"))
        if not avi_files:
            pytest.skip("No .avi files under the miniscope fixture directory.")

    def test_miniscope_pipeline_end_to_end(self, mock_data_exists, monkeypatch):
        """
        Run the full Miniscope Pipeline on a tiny sample movie and verify output quality.
        """
        print("DEBUG: Setting up mock pipeline...", flush=True)

        def mock_create(line_num, filenames, auto_import_data):
            dm = UCLADataManager(line_num=line_num, auto_import_data=False)
            dm.metadata = {"id": "test_mouse", "calcium imaging directory": MINISCOPE_DIR}
            if hasattr(dm, "filenames"):
                dm.filenames = filenames
            dm.load_attributes([MINISCOPE_DIR / str(f) for f in filenames])
            return dm

        monkeypatch.setattr(
            "ace_neuro.shared.csv_worker.CSVWorker.csv_row_to_dict",
            lambda *args, **kwargs: {"id": "test_mouse", "calcium imaging directory": MINISCOPE_DIR},
        )
        monkeypatch.setattr("ace_neuro.shared.file_downloader.verify_file_by_line", lambda *args, **kwargs: None)
        monkeypatch.setattr(
            "ace_neuro.miniscope.miniscope_data_manager.MiniscopeDataManager.create", mock_create
        )

        print("DEBUG: Instantiating MiniscopePipeline...", flush=True)
        api = MiniscopePipeline()

        print("DEBUG: Preparing run kwargs...", flush=True)

        run_kwargs = MOCK_ANALYSIS_PARAMS.copy()

        avi_file = list(MINISCOPE_DIR.glob("*.avi"))[0]
        run_kwargs["filenames"] = [avi_file.name]

        monkeypatch.setattr("ace_neuro.pipelines.miniscope.update_csv_cell", lambda *args, **kwargs: None)

        print(f"DEBUG: Running api.run with kwargs: {run_kwargs}", flush=True)
        try:
            api.run(line_num=999, **run_kwargs)
            print("DEBUG: api.run completed successfully!", flush=True)
        except Exception as e:
            pytest.fail(f"Pipeline execution failed: {e}")

        estimates_path = MINISCOPE_DIR / "saved_movies" / "test_estimates.hdf5"
        assert estimates_path.exists(), f"CNMF-E estimates file was not generated at {estimates_path}."

        with h5py.File(estimates_path, "r") as f:
            assert "estimates" in f, "HDF5 is missing 'estimates' group."

            if "C" in f["estimates"]:
                C = np.array(f["estimates"]["C"])
                assert C.shape[0] > 0, "No components found (C array is empty)."
                assert not np.isnan(C).any(), "NaN values found in calcium traces."
                assert not np.isinf(C).any(), "Inf values found in calcium traces."

            if "A" in f["estimates"]:
                A_data = np.array(f["estimates"]["A"]["data"])
                assert len(A_data) > 0, "Spatial components are empty."

        events_csv = list(MINISCOPE_DIR.glob("*events*.csv"))
        if events_csv:
            assert events_csv[0].stat().st_size > 0, "Events CSV was generated but is empty."
