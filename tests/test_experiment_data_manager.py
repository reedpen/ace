from unittest.mock import patch

import pytest

from ace_neuro.shared.experiment_data_manager import ExperimentDataManager


class TestExperimentDataManager:
    @patch("ace_neuro.shared.experiment_data_manager.CSVWorker")
    def test_import_metadata_success(self, mock_csv_worker, tmp_path):
        # Create a fake experiments.csv so the exists() check passes
        experiments_csv = tmp_path / "experiments.csv"
        experiments_csv.touch()

        mock_csv_worker.csv_row_to_dict.return_value = {"id": "test_exp", "ephys directory": "test_dir"}
        mock_csv_worker.convert_data_types.return_value = {"id": "test_exp", "ephys directory": "test_dir"}

        # Initialize manager with explicit project_path
        manager = ExperimentDataManager(
            line_num=1, project_path=tmp_path,
            auto_import_metadata=False, auto_import_analysis_params=False
        )
        manager.import_metadata()

        assert manager.metadata is not None
        assert manager.metadata["id"] == "test_exp"
        # The path should've been appended with data_path, so it is a PosixPath now
        assert "test_dir" in str(manager.metadata["ephys directory"])

    def test_import_metadata_missing_file(self, tmp_path):
        manager = ExperimentDataManager(
            line_num=1, project_path=tmp_path,
            auto_import_metadata=False, auto_import_analysis_params=False
        )

        with pytest.raises(FileNotFoundError, match="Did you forget to initialize your project data folder"):
            manager.import_metadata()

    @patch("ace_neuro.shared.experiment_data_manager.CSVWorker")
    def test_import_analysis_parameters_success(self, mock_csv_worker, tmp_path):
        # Create a fake analysis_parameters.csv
        analysis_csv = tmp_path / "analysis_parameters.csv"
        analysis_csv.touch()

        mock_csv_worker.csv_row_to_dict.return_value = {"parallel": True}
        mock_csv_worker.convert_data_types.return_value = {"parallel": True}

        manager = ExperimentDataManager(
            line_num=1, project_path=tmp_path,
            auto_import_metadata=False, auto_import_analysis_params=False
        )
        manager.import_analysis_parameters()

        assert manager.analysis_params == {"parallel": True}
