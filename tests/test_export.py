"""Tests for WAV export functionality."""

import pytest
import numpy as np
from scipy.io import wavfile
import tempfile
import os
from toneflow.audio.export_wav import export_wav


def test_export_creates_valid_wav():
    """Test that export creates a valid WAV file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test.wav")
        
        # Export a short file (0.5 min = 30 sec)
        export_wav(
            carrier_hz=500.0,
            beat_hz=10.0,
            mode='binaural',
            duration_min=0.5,
            output_path=output_path,
            effects_config={
                'reverb': {'enabled': False},
                'noise': {'enabled': False}
            },
            sample_rate=44100
        )
        
        # Check file exists
        assert os.path.exists(output_path)
        
        # Load and verify
        rate, data = wavfile.read(output_path)
        
        # Check sample rate
        assert rate == 44100
        
        # Check duration (30 seconds = 1,323,000 samples at 44.1kHz)
        expected_samples = int(30 * 44100)
        assert data.shape[0] == expected_samples
        
        # Check stereo
        assert data.shape[1] == 2
        
        # Check data type
        assert data.dtype == np.int16


def test_export_with_effects():
    """Test export with effects enabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_fx.wav")
        
        export_wav(
            carrier_hz=512.0,
            beat_hz=10.0,
            mode='binaural',
            duration_min=0.1,  # Very short for test
            output_path=output_path,
            effects_config={
                'reverb': {'enabled': True, 'wet_dry': 0.35},
                'noise': {'enabled': True, 'type': 'pink', 'level_dbfs': -20.0}
            },
            sample_rate=44100
        )
        
        assert os.path.exists(output_path)
        
        # Verify it's readable
        rate, data = wavfile.read(output_path)
        assert rate == 44100
        assert data.shape[1] == 2


def test_export_monaural_mode():
    """Test export in monaural mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_mono.wav")
        
        export_wav(
            carrier_hz=440.0,
            beat_hz=6.0,
            mode='monaural',
            duration_min=0.1,
            output_path=output_path,
            effects_config={
                'reverb': {'enabled': False},
                'noise': {'enabled': False}
            },
            sample_rate=44100
        )
        
        rate, data = wavfile.read(output_path)
        
        # Monaural should have identical channels (after effects/limiter)
        # Check correlation
        correlation = np.corrcoef(data[:, 0], data[:, 1])[0, 1]
        assert correlation > 0.99  # Very high correlation for monaural


def test_export_duration_accuracy():
    """Test that export duration is accurate."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_duration.wav")
        
        duration_min = 0.25  # 15 seconds
        
        export_wav(
            carrier_hz=500.0,
            beat_hz=10.0,
            mode='binaural',
            duration_min=duration_min,
            output_path=output_path,
            effects_config={
                'reverb': {'enabled': False},
                'noise': {'enabled': False}
            },
            sample_rate=44100
        )
        
        rate, data = wavfile.read(output_path)
        
        expected_samples = int(duration_min * 60 * 44100)
        assert data.shape[0] == expected_samples


def test_export_no_clipping():
    """Test that exported audio doesn't clip."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_clip.wav")
        
        export_wav(
            carrier_hz=600.0,
            beat_hz=40.0,
            mode='binaural',
            duration_min=0.1,
            output_path=output_path,
            effects_config={
                'reverb': {'enabled': True, 'wet_dry': 0.5},
                'noise': {'enabled': True, 'type': 'white', 'level_dbfs': -10.0}
            },
            sample_rate=44100
        )
        
        rate, data = wavfile.read(output_path)
        
        # Check no clipping (int16 range is -32768 to 32767)
        assert np.all(data > -32768)
        assert np.all(data < 32767)

        # Check that limiter kept peaks below -1 dBFS (linear ceiling)
        threshold = int(32767 * 10 ** (-1.0 / 20.0))
        assert np.max(np.abs(data)) <= threshold * 1.02


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

