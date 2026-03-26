"""Tests for structured exception handling across pipeline entry points."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ace_neuro.pipelines.ephys import EphysPipeline
from ace_neuro.pipelines.miniscope import MiniscopePipeline
from ace_neuro.pipelines.multimodal import MultimodalPipeline
from ace_neuro.shared.exceptions import (
    DataNotFoundError,
    PipelineExecutionError,
    format_error_message,
)


def test_format_error_message_includes_context_and_hint() -> None:
    err = PipelineExecutionError(
        "Processing failed.",
        stage="run_cnmfe",
        line_num=7,
        project_path=Path("/tmp/project"),
        data_path=Path("/tmp/data"),
        hint="Check CNMF-E parameters.",
    )
    msg = format_error_message(err)
    assert "PipelineExecutionError: Processing failed." in msg
    assert "stage=run_cnmfe" in msg
    assert "line_num=7" in msg
    assert "project_path=/tmp/project" in msg
    assert "data_path=/tmp/data" in msg
    assert "Next action: Check CNMF-E parameters." in msg


@patch("ace_neuro.pipelines.miniscope.MiniscopeDataManager.create")
def test_miniscope_wraps_missing_data_as_data_not_found(mock_create: MagicMock) -> None:
    mock_create.side_effect = FileNotFoundError("missing miniscope file")
    api = MiniscopePipeline()
    with pytest.raises(DataNotFoundError, match="Required miniscope input files were not found"):
        api.run(line_num=1, headless=True, filenames=["0.avi"])


@patch("ace_neuro.pipelines.ephys.ExperimentDataManager")
def test_ephys_wraps_missing_metadata_as_data_not_found(mock_edm: MagicMock) -> None:
    mock_edm.side_effect = FileNotFoundError("experiments.csv missing")
    api = EphysPipeline()
    with pytest.raises(DataNotFoundError, match="Project metadata files were not found"):
        api.run(line_num=1, headless=True)


@patch("ace_neuro.pipelines.multimodal.EphysPipeline.run")
def test_multimodal_wraps_subpipeline_error_with_stage(mock_ephys_run: MagicMock) -> None:
    mock_ephys_run.side_effect = ValueError("bad channel")
    api = MultimodalPipeline()
    with pytest.raises(PipelineExecutionError, match="failed during ephys sub-pipeline"):
        api.run(line_num=1, headless=True, miniscope_filenames=["0.avi"])
