import pytest
from pathlib import Path
import os
import numpy as np
import h5py
from typing import Any
from ace_neuro.pipelines.miniscope import MiniscopePipeline
from ace_neuro.shared.experiment_data_manager import ExperimentDataManager
from ace_neuro.miniscope.miniscope_data_manager import MiniscopeDataManager
from ace_neuro.miniscope.ucla_data_manager import UCLADataManager
from ace_neuro.pipelines.ephys import EphysPipeline

# Define paths for our mock dataset
TEST_DATA_DIR = Path(__file__).parent / "data" / "sample_recording"
MINISCOPE_DIR = TEST_DATA_DIR / "UCLA and Neuralynx" / "miniscope"
EPHYS_DIR = TEST_DATA_DIR / "UCLA and Neuralynx" / "ephys"

# We assume a mock experiment parameters CSV will exist in the tests directory or we can inject parameters
MOCK_ANALYSIS_PARAMS: dict[str, Any] = {
    'crop': False,
    'detrend_method': 'median',
    'df_over_f': True,
    'secs_window': 5,
    'quantile_min': 8,
    'df_over_f_method': 'delta_f_over_sqrt_f',
    'parallel': False, # Keep single-threaded for tests
    'n_processes': 1,
    'apply_motion_correction': False, # Skip for speed unless we have a specific mock for it
    'inspect_motion_correction': False,
    'plot_params': False,
    'run_CNMFE': True,
    'save_estimates': True,
    'save_CNMFE_estimates_filename': 'test_estimates.hdf5',
    'save_CNMFE_params': False,
    'remove_components_with_gui': False, # Must be False for headless CI
    'find_calcium_events': True,
    'derivative_for_estimates': 'first',
    'event_height': 5,
    'compute_miniscope_phase': False, # Simplify for minimal test
    'filter_miniscope_data': False, # Simplify for minimal test
    'compute_miniscope_spectrogram': False, # Simplify for minimal test
    'headless': True
}

class TestEndToEndPipeline:
    
    @pytest.fixture
    def mock_data_exists(self):
        """Fixture to check if the user has downloaded/generated the mock data yet."""
        if not MINISCOPE_DIR.exists() or not EPHYS_DIR.exists():
            pytest.skip("Mock data directories do not exist. Please generate the mock data first.")
            
        avi_files = list(MINISCOPE_DIR.glob("*.avi"))
        if not avi_files:
            pytest.skip("No .avi files found in the mock miniscope directory.")
            
    def test_miniscope_pipeline_end_to_end(self, mock_data_exists, tmp_path, monkeypatch):
        """
        Run the full Miniscope Pipeline on a tiny sample movie and verify output quality.
        """
        # 1. Setup Mock project paths
        # Paths are now always explicit — no .env or globals to patch.
        # We construct the specific DataManager manually for testing.
        print("DEBUG: Setting up mock pipeline...", flush=True)

        
        # We patch MiniscopeDataManager.create to return our explicitly configured manager
        # Since create() decides between Onix and UCLA, we'll force a UCLA one for now to read the dir
        def mock_create(line_num, filenames, auto_import_data):
            dm = UCLADataManager(line_num=line_num, auto_import_data=False)
            dm.metadata = {
                'id': 'test_mouse',
                'calcium imaging directory': MINISCOPE_DIR
            }
            if hasattr(dm, 'filenames'):
                dm.filenames = filenames
            # Import data manually
            dm.load_attributes([MINISCOPE_DIR / str(f) for f in filenames])
            return dm
            
        monkeypatch.setattr("ace_neuro.shared.csv_worker.CSVWorker.csv_row_to_dict", lambda *args, **kwargs: {'id': 'test_mouse', 'calcium imaging directory': MINISCOPE_DIR})
        monkeypatch.setattr("ace_neuro.shared.file_downloader.verify_file_by_line", lambda *args, **kwargs: None)
        monkeypatch.setattr("ace_neuro.miniscope.miniscope_data_manager.MiniscopeDataManager.create", mock_create)
        
        # 2. Run the pipeline headlessly
        print("DEBUG: Instantiating MiniscopePipeline...", flush=True)
        api = MiniscopePipeline()
        
        # Pass a dummy line number, we patched create() anyway.
        # Update our kwargs with the filenames
        print("DEBUG: Preparing run kwargs...", flush=True)

        run_kwargs = MOCK_ANALYSIS_PARAMS.copy()
        
        # Get the first avi file name
        # Assuming our pipeline takes just ['0.avi'] or similar
        avi_file = list(MINISCOPE_DIR.glob("*.avi"))[0]
        run_kwargs['filenames'] = [avi_file.name]
        
        # We also need to patch update_csv_cell so it doesn't try to write to a real analysis_params.csv
        monkeypatch.setattr("ace_neuro.pipelines.miniscope.update_csv_cell", lambda *args, **kwargs: None)
        
        # Run it!
        print(f"DEBUG: Running api.run with kwargs: {run_kwargs}", flush=True)
        try:
            api.run(line_num=999, **run_kwargs)
            print("DEBUG: api.run completed successfully!", flush=True)
        except Exception as e:
            pytest.fail(f"Pipeline execution failed: {e}")
            
        # 3. Verify Output Quality
        
        # Verify estimates.hdf5 was created
        estimates_path = MINISCOPE_DIR / "saved_movies" / "test_estimates.hdf5"
        assert estimates_path.exists(), f"CNMF-E estimates file was not generated at {estimates_path}."
        
        # Open HDF5 and inspect traces
        with h5py.File(estimates_path, 'r') as f:
            # Check for standard CaImAn CNMFE datasets
            assert 'estimates' in f, "HDF5 is missing 'estimates' group."
            
            # Verify traces (C or F_dff) are not empty and have plausible values
            if 'C' in f['estimates']:
                C = np.array(f['estimates']['C'])
                assert C.shape[0] > 0, "No components found (C array is empty)."
                # basic plausibility
                assert not np.isnan(C).any(), "NaN values found in calcium traces."
                assert not np.isinf(C).any(), "Inf values found in calcium traces."
                
            # Verify spatial footprints (A)
            if 'A' in f['estimates']:
                A_data = np.array(f['estimates']['A']['data'])
                assert len(A_data) > 0, "Spatial components are empty."
                
        # Check if events CSV was generated (if your pipeline saves them to MINISCOPE_DIR)
        events_csv = list(MINISCOPE_DIR.glob("*events*.csv"))
        if events_csv:
            assert events_csv[0].stat().st_size > 0, "Events CSV was generated but is empty."
