from unittest.mock import patch

from ace_neuro.ephys.neuralynx_data_manager import NeuralynxDataManager
from ace_neuro.miniscope.ucla_data_manager import UCLADataManager


class TestSync:
    def test_neuralynx_instantiation(self):
        """Test that NeuralynxDataManager can be instantiated with minimal args."""
        ephys_dm = NeuralynxDataManager(
            ephys_directory=None,
            auto_import_ephys_block=False,
            auto_process_block=False,
            auto_compute_phases=False
        )
        assert ephys_dm is not None

    @patch("ace_neuro.miniscope.miniscope_data_manager.MiniscopeDataManager._find_movie_file_paths", return_value=[])
    @patch("ace_neuro.shared.file_downloader.verify_file_by_line")
    @patch("ace_neuro.shared.csv_worker.CSVWorker.csv_row_to_dict")
    def test_ucla_instantiation(self, mock_csv_row, mock_verify, mock_find_movies, tmp_path):
        """Test that UCLADataManager can be instantiated with minimal args."""
        # Mock the metadata return to avoid dependency on a real CSV
        mock_csv_row.return_value = {
            'id': 'test_mouse',
            'calcium imaging directory': 'test_dir'
        }
        mock_verify.return_value = None

        # Using a valid line number might be tricky without a real experiments.csv
        # if the __init__ requires it. Assuming auto_import_data=False avoids it.
        miniscope_dm = UCLADataManager(
            line_num=97,
            auto_import_data=False
        )
        assert miniscope_dm is not None
