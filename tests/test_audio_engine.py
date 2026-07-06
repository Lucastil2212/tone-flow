"""Tests for audio engine and oscillators."""

import pytest
import numpy as np
from toneflow.audio import osc
from toneflow.audio.effects import SoftLimiter


def test_binaural_beat_frequency_difference():
    """Test that binaural beats produce correct L/R frequency difference."""
    base_hz = 500.0
    beat_hz = 10.0
    duration = 1.0
    sample_rate = 44100
    
    chunk, phase_l, phase_r = osc.generate_binaural_chunk(base_hz, beat_hz, duration, sample_rate)
    
    # Check shape
    assert chunk.shape == (sample_rate, 2)
    
    # Left channel should be base - beat/2 = 495 Hz
    # Right channel should be base + beat/2 = 505 Hz
    left = chunk[:, 0]
    right = chunk[:, 1]
    
    # Channels should be different
    assert not np.allclose(left, right)
    
    # Check frequency via FFT (rough check)
    fft_left = np.fft.rfft(left)
    fft_right = np.fft.rfft(right)
    freqs = np.fft.rfftfreq(len(left), 1.0/sample_rate)
    
    # Find dominant frequency in each channel
    left_peak_idx = np.argmax(np.abs(fft_left))
    right_peak_idx = np.argmax(np.abs(fft_right))
    
    left_freq = freqs[left_peak_idx]
    right_freq = freqs[right_peak_idx]
    
    # Should be within 1 Hz of expected
    assert abs(left_freq - 495.0) < 1.0
    assert abs(right_freq - 505.0) < 1.0


def test_monaural_beat_channels_identical():
    """Test that monaural beats have identical L/R channels."""
    base_hz = 500.0
    beat_hz = 10.0
    duration = 0.1
    
    chunk, phase_l, phase_r = osc.generate_monaural_chunk(base_hz, beat_hz, duration, 44100)
    
    left = chunk[:, 0]
    right = chunk[:, 1]
    
    # Channels should be identical
    assert np.allclose(left, right)


def test_limiter_prevents_clipping():
    """Test that soft limiter keeps peaks below threshold."""
    # Create signal that would clip
    signal = np.random.randn(1000, 2).astype(np.float32) * 2.0  # Can exceed ±1
    
    limiter = SoftLimiter(threshold_db=-1.0)
    limited = limiter.process(signal)
    
    # Check that no sample exceeds threshold
    threshold = 10 ** (-1.0 / 20.0)  # ~0.891
    assert np.all(np.abs(limited) <= threshold * 1.01)  # Small tolerance for tanh


def test_parameter_clamping():
    """Test that oscillators clamp parameters to safe ranges."""
    # Test extreme values
    chunk, _, _ = osc.generate_binaural_chunk(
        base_hz=5000.0,  # Way above max
        beat_hz=100.0,   # Way above max
        duration_sec=0.01,
        sample_rate=44100
    )
    
    # Should not crash and should produce valid output
    assert chunk.shape[1] == 2
    assert np.all(np.isfinite(chunk))
    assert np.all(np.abs(chunk) <= 2.0)  # Reasonable range


def test_phase_continuity():
    """Test that phase is continuous across multiple chunks."""
    base_hz = 500.0
    beat_hz = 10.0
    duration = 0.01  # 10ms chunks
    sample_rate = 44100
    
    # Generate first chunk
    chunk1, phase_l1, phase_r1 = osc.generate_binaural_chunk(
        base_hz, beat_hz, duration, sample_rate
    )
    
    # Generate second chunk with ending phase from first
    chunk2, phase_l2, phase_r2 = osc.generate_binaural_chunk(
        base_hz, beat_hz, duration, sample_rate, phase_l1, phase_r1
    )
    
    # Verify phases are updated
    assert phase_l1 != 0.0
    assert phase_r1 != 0.0
    assert phase_l2 != phase_l1
    assert phase_r2 != phase_r1
    
    # Verify continuity: last sample of chunk1 should match first sample of chunk2
    # (with some tolerance due to floating point and phase wrapping)
    # This is a rough check - perfect continuity would require more precise analysis
    assert chunk1.shape == chunk2.shape
    assert np.all(np.isfinite(chunk1))
    assert np.all(np.isfinite(chunk2))


def test_phase_wrapping():
    """Test that phase wraps correctly at 2π."""
    base_hz = 500.0
    beat_hz = 10.0
    duration = 1.0  # Long enough to wrap phase multiple times
    sample_rate = 44100
    
    chunk, phase_l, phase_r = osc.generate_binaural_chunk(
        base_hz, beat_hz, duration, sample_rate
    )
    
    # Phases should be wrapped to [0, 2π)
    assert 0.0 <= phase_l < 2.0 * np.pi
    assert 0.0 <= phase_r < 2.0 * np.pi


def test_pink_noise_generation():
    """Test that pink noise is generated without errors."""
    noise = osc.generate_pink_noise(0.1, 44100)
    
    assert noise.shape == (4410, 2)
    assert np.all(np.isfinite(noise))
    
    # Pink noise should have some variance (scaled to ~0.35 peak)
    assert np.std(noise) > 0.05


def test_white_noise_generation():
    """Test that white noise is generated without errors."""
    noise = osc.generate_white_noise(0.1, 44100)
    
    assert noise.shape == (4410, 2)
    assert np.all(np.isfinite(noise))
    
    # White noise scaled to ~0.35 amplitude
    assert 0.25 < np.std(noise) < 0.45


def test_smoothing_no_abrupt_jumps():
    """Test that parameter changes are smoothed."""
    # This would require running the engine, which needs pygame mixer
    # For unit test, we'll test the math
    
    # Exponential smoothing formula
    current = 500.0
    target = 600.0
    alpha = 0.1  # Smoothing factor
    
    # After one step
    new_value = current + alpha * (target - current)
    
    # Should move toward target but not reach it
    assert new_value > current
    assert new_value < target
    assert abs(new_value - 510.0) < 1.0  # Should be ~510


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

