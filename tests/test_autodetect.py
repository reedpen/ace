import pytest
from pathlib import Path
from unittest.mock import patch

from ace_neuro.miniscope.miniscope_data_manager import MiniscopeDataManager
from ace_neuro.miniscope.ucla_data_manager import UCLADataManager
from ace_neuro.miniscope.onix_miniscope_data_manager import OnixMiniscopeDataManager

from ace_neuro.ephys.ephys_data_manager import EphysDataManager
from ace_neuro.ephys.neuralynx_data_manager import NeuralynxDataManager
from ace_neuro.ephys.rhs2116_data_manager import RHS2116DataManager

TEST_DOC_DIR = Path(__file__).parent / "data" / "sample_recording"

@patch("ace_neuro.shared.experiment_data_manager.ExperimentDataManager.__init__")
@patch("ace_neuro.shared.experiment_data_manager.ExperimentDataManager.get_miniscope_directory")
def test_miniscope_autodetect_ucla(mock_get_dir, mock_init):
    # Mock the initialization to avoid reading experiments.csv
    mock_init.return_value = None
    # Provide the path to the UCLA miniscope test data
    mock_get_dir.return_value = str(TEST_DOC_DIR / "UCLA and Neuralynx" / "miniscope")
    
    # We patch __init__ for the subclasses as well, so they don't try to load their __init__ components which call super().__init__ which is patched
    with patch("ace_neuro.miniscope.ucla_data_manager.UCLADataManager.__init__", return_value=None):
        dm = MiniscopeDataManager.create(line_num=1, auto_import_data=False)
        assert isinstance(dm, UCLADataManager)

@patch("ace_neuro.shared.experiment_data_manager.ExperimentDataManager.__init__")
@patch("ace_neuro.shared.experiment_data_manager.ExperimentDataManager.get_miniscope_directory")
def test_miniscope_autodetect_onix(mock_get_dir, mock_init):
    mock_init.return_value = None
    mock_get_dir.return_value = str(TEST_DOC_DIR / "ONIX")
    
    with patch("ace_neuro.miniscope.onix_miniscope_data_manager.OnixMiniscopeDataManager.__init__", return_value=None):
        dm = MiniscopeDataManager.create(line_num=1, auto_import_data=False)
        assert isinstance(dm, OnixMiniscopeDataManager)

def test_ephys_autodetect_neuralynx():
    ephys_dir = str(TEST_DOC_DIR / "UCLA and Neuralynx" / "ephys")
    with patch("ace_neuro.ephys.neuralynx_data_manager.NeuralynxDataManager.__init__", return_value=None):
        dm = EphysDataManager.create(ephys_directory=ephys_dir, auto_import_ephys_block=False, auto_process_block=False, auto_compute_phases=False)
        assert isinstance(dm, NeuralynxDataManager)

def test_ephys_autodetect_onix():
    onix_dir = str(TEST_DOC_DIR / "ONIX")
    with patch("ace_neuro.ephys.rhs2116_data_manager.RHS2116DataManager.__init__", return_value=None):
        dm = EphysDataManager.create(ephys_directory=onix_dir, auto_import_ephys_block=False, auto_process_block=False, auto_compute_phases=False)
        assert isinstance(dm, RHS2116DataManager)
