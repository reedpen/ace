"""Unit tests for MiniscopePipeline wiring without running CaImAn CNMF-E."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from ace_neuro.pipelines.miniscope import MiniscopePipeline


@patch("ace_neuro.pipelines.miniscope.update_csv_cell")
@patch("ace_neuro.pipelines.miniscope.MiniscopePostprocessor")
@patch("ace_neuro.pipelines.miniscope.MiniscopeProcessor")
@patch("ace_neuro.pipelines.miniscope.MiniscopePreprocessor")
@patch("ace_neuro.pipelines.miniscope.MiniscopeDataManager.create")
def test_run_skips_postprocess_when_cnmfe_none(
    mock_create: MagicMock,
    mock_pre_class: MagicMock,
    mock_proc_class: MagicMock,
    mock_post_class: MagicMock,
    mock_update_csv: MagicMock,
) -> None:
    """When CNMF-E does not run, CNMFE_obj stays None and postprocess is not constructed."""
    dm = MagicMock()
    dm.coords = None
    dm.CNMFE_obj = None
    dm.project_path = Path("/tmp/fake_project")

    mock_create.return_value = dm
    pre = MagicMock()
    pre.preprocess_calcium_movie.return_value = dm
    mock_pre_class.return_value = pre

    proc = MagicMock()
    proc.process_calcium_movie.return_value = dm
    mock_proc_class.return_value = proc

    api = MiniscopePipeline()
    api.run(
        line_num=1,
        filenames=["0.avi"],
        headless=True,
        run_CNMFE=False,
        save_estimates=False,
    )

    mock_post_class.assert_not_called()
    mock_update_csv.assert_not_called()


@patch("ace_neuro.pipelines.miniscope.update_csv_cell")
@patch("ace_neuro.pipelines.miniscope.MiniscopePostprocessor")
@patch("ace_neuro.pipelines.miniscope.MiniscopeProcessor")
@patch("ace_neuro.pipelines.miniscope.MiniscopePreprocessor")
@patch("ace_neuro.pipelines.miniscope.MiniscopeDataManager.create")
def test_headless_forces_no_gui_flags(
    mock_create: MagicMock,
    mock_pre_class: MagicMock,
    mock_proc_class: MagicMock,
    mock_post_class: MagicMock,
    mock_update_csv: MagicMock,
) -> None:
    """Headless mode should not request GUI steps from the processor."""
    dm = MagicMock()
    dm.coords = None
    dm.CNMFE_obj = None
    dm.project_path = Path("/tmp/fake_project")

    mock_create.return_value = dm
    pre = MagicMock()
    pre.preprocess_calcium_movie.return_value = dm
    mock_pre_class.return_value = pre

    proc = MagicMock()
    proc.process_calcium_movie.return_value = dm
    mock_proc_class.return_value = proc

    api = MiniscopePipeline()
    api.run(
        line_num=1,
        filenames=["0.avi"],
        headless=True,
        run_CNMFE=False,
        inspect_motion_correction=True,
        remove_components_with_gui=True,
        plot_params=True,
        save_estimates=False,
    )

    call_kw = proc.process_calcium_movie.call_args
    assert call_kw is not None
    # parallel, n_processes, apply_motion_correction, inspect_motion_correction, plot_params, ...
    assert call_kw[0][3] is False  # inspect_motion_correction forced off in headless
