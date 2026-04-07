"""Frame-period helpers for miniscope acquisition and TTL sync."""

from __future__ import annotations

from typing import Any, Dict, Optional

DEFAULT_MINISCOPE_FRAME_RATE_HZ = 30.0
"""Fallback when metadata does not specify frameRate (legacy behavior)."""

TTL_GAP_THRESHOLD_FRAME_MULTIPLE = 1.5
"""Inter-TTL gaps longer than this many frame periods flag missing pulses."""


def resolve_miniscope_frame_rate_hz(
    metadata: Optional[Dict[str, Any]],
    fr: Optional[float] = None,
) -> float:
    """Return a positive imaging frame rate (Hz) from metadata or attributes."""
    if metadata is not None and "frameRate" in metadata:
        rate = float(metadata["frameRate"])
    elif fr is not None:
        rate = float(fr)
    else:
        rate = DEFAULT_MINISCOPE_FRAME_RATE_HZ
    if rate <= 0:
        raise ValueError(
            "Miniscope frame rate must be positive for frame-based timing; "
            f"got frameRate={rate!r}."
        )
    return rate


def frame_period_seconds(frame_rate_hz: float) -> float:
    """Duration of one imaging frame in seconds."""
    return 1.0 / float(frame_rate_hz)


def ttl_gap_threshold_seconds(
    frame_rate_hz: float,
    frame_multiple: float = TTL_GAP_THRESHOLD_FRAME_MULTIPLE,
) -> float:
    """Threshold (seconds): adjacent TTL onsets farther apart imply dropped frame(s)."""
    return float(frame_multiple) / float(frame_rate_hz)
