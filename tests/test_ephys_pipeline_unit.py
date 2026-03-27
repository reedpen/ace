"""Unit tests for EphysPipeline.run with mocked I/O and ephys backends."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from ace_neuro.ephys.channel import Channel
from ace_neuro.pipelines.ephys import EphysPipeline


@patch("ace_neuro.pipelines.ephys.ChannelWorker")
@patch("ace_neuro.pipelines.ephys.EphysDataManager.create")
@patch("ace_neuro.pipelines.ephys.file_downloader.verify_file_by_line")
@patch("ace_neuro.pipelines.ephys.ExperimentDataManager")
def test_ephys_run_headless_skips_plots(
    mock_edm: MagicMock,
    mock_verify: MagicMock,
    mock_create: MagicMock,
    mock_cw: MagicMock,
) -> None:
    edm = mock_edm.return_value
    edm.get_ephys_directory.return_value = "/fake/ephys"

    ch = Channel(
        name="PFCLFPvsCBEEG",
        signal=np.zeros(100),
        sampling_rate=1000.0,
        time_vector=np.arange(100) / 1000.0,
        events={"labels": np.array([]), "timestamps": np.array([])},
    )
    dm = MagicMock()
    dm.channels = {"PFCLFPvsCBEEG": ch}
    dm.get_channel.return_value = ch
    mock_create.return_value = dm

    api = EphysPipeline()
    api.run(
        line_num=1,
        headless=True,
        plot_channel=True,
        plot_spectrogram=True,
        plot_phases=True,
        filter_type=None,
    )

    cw = mock_cw.return_value
    cw.plot_channel.assert_not_called()
    cw.plot_spectrogram.assert_not_called()
    cw.plot_phases.assert_not_called()


@patch("ace_neuro.pipelines.ephys.ChannelWorker")
@patch("ace_neuro.pipelines.ephys.EphysDataManager.create")
@patch("ace_neuro.pipelines.ephys.file_downloader.verify_file_by_line")
@patch("ace_neuro.pipelines.ephys.ExperimentDataManager")
def test_ephys_run_loads_channel_and_creates_worker(
    mock_edm: MagicMock,
    mock_verify: MagicMock,
    mock_create: MagicMock,
    mock_cw: MagicMock,
) -> None:
    edm = mock_edm.return_value
    edm.get_ephys_directory.return_value = "/fake/ephys"

    ch = Channel(
        name="PFCLFPvsCBEEG",
        signal=np.zeros(100),
        sampling_rate=1000.0,
        time_vector=np.arange(100) / 1000.0,
        events={"labels": np.array([]), "timestamps": np.array([])},
    )
    dm = MagicMock()
    dm.channels = {"PFCLFPvsCBEEG": ch}
    dm.get_channel.return_value = ch
    mock_create.return_value = dm

    api = EphysPipeline()
    api.run(line_num=1, headless=True, filter_type=None)

    dm.get_channel.assert_called_once_with("PFCLFPvsCBEEG")
    mock_cw.assert_called_once()


@patch("ace_neuro.pipelines.ephys.ExperimentDataManager")
def test_ephys_run_raises_when_no_ephys_directory(mock_edm: MagicMock) -> None:
    edm = mock_edm.return_value
    edm.get_ephys_directory.return_value = None

    api = EphysPipeline()
    with patch("ace_neuro.pipelines.ephys.file_downloader.verify_file_by_line"):
        with pytest.raises(ValueError, match="Ephys directory could not be determined"):
            api.run(line_num=1, headless=True)
