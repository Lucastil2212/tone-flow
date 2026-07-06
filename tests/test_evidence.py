"""Tests for EEG band and evidence helpers."""

from toneflow.presets.evidence import (
    band_for_beat,
    beat_in_band,
    EEG_BANDS,
    SCHUMANN_FUNDAMENTAL_HZ,
)
from toneflow.presets.catalog import PRESETS


def test_standard_bands():
    assert band_for_beat(2.0) == 'delta'
    assert band_for_beat(6.0) == 'theta'
    assert band_for_beat(10.0) == 'alpha'
    assert band_for_beat(18.0) == 'beta'
    assert band_for_beat(40.0) == 'gamma'


def test_schumann_beat():
    assert band_for_beat(7.83) == 'schumann'
    assert beat_in_band(7.83, 'schumann')


def test_all_presets_match_declared_band():
    for preset in PRESETS:
        band = preset['eeg_band']
        beat = preset['beat_hz']
        if band == 'alpha_theta':
            assert 7.5 <= beat <= 8.5
        elif band == 'schumann':
            assert abs(beat - SCHUMANN_FUNDAMENTAL_HZ) < 0.01
        else:
            assert beat_in_band(beat, band), f"{preset['id']}: {beat} vs {band}"
