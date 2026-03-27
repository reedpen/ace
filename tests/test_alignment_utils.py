"""Tests for multimodal alignment helpers (pure numpy / Channel)."""

from __future__ import annotations

import numpy as np

from ace_neuro.ephys.channel import Channel
from ace_neuro.multimodal.miniscope_ephys_alignment_utils import find_ephys_idx_of_TTL_events


def test_find_ephys_idx_of_TTL_events_matches_nearest_sample() -> None:
    """TTL times should map to closest ephys sample indices."""
    fs = 1000.0
    n = 5000
    time_vector = np.arange(n) / fs
    ch = Channel(
        name="ttl",
        signal=np.zeros(n),
        sampling_rate=fs,
        time_vector=time_vector,
        events={"labels": np.array([]), "timestamps": np.array([])},
    )
    t_ca = np.array([0.0, 0.001, 0.010])
    idx, _ = find_ephys_idx_of_TTL_events(
        t_ca, ch, frame_rate=30.0, ca_events_idx=None, all_TTL_events=True
    )
    assert idx is not None
    assert np.allclose(idx, [0, 1, 10])
