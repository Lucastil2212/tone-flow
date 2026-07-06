"""Oscillators — per-sample phase integration for click-free, clean output."""

import numpy as np

BINAURAL_AMP = 0.85
MONAURAL_AMP = 0.42
ISOCHRONIC_AMP = 0.80


def _n_samples(duration_sec, sample_rate):
    return max(1, int(round(duration_sec * sample_rate)))


def _integrate_phases(freq_hz, n_samples, sample_rate, phase_start):
    inc = (2.0 * np.pi * freq_hz / sample_rate).astype(np.float64)
    return phase_start + np.cumsum(inc)


def _ramp_freq(start_hz, end_hz, n_samples):
    if n_samples <= 1:
        return np.full(n_samples, end_hz, dtype=np.float64)
    t = np.linspace(0.0, 1.0, n_samples, dtype=np.float64)
    return start_hz + (end_hz - start_hz) * t


def _sine(phases):
    return np.sin(phases).astype(np.float32)


def _end_phase(phases):
    return float(phases[-1] % (2.0 * np.pi))


def _binaural_ramped(c0, c1, b0, b1, n_samples, sample_rate, pl, pr):
    c0, c1 = np.clip(c0, 100.0, 1000.0), np.clip(c1, 100.0, 1000.0)
    b0, b1 = np.clip(b0, 0.0, 40.0), np.clip(b1, 0.0, 40.0)

    carrier = _ramp_freq(c0, c1, n_samples)
    beat = _ramp_freq(b0, b1, n_samples)
    f_l = carrier - beat * 0.5
    f_r = carrier + beat * 0.5

    phases_l = _integrate_phases(f_l, n_samples, sample_rate, pl)
    phases_r = _integrate_phases(f_r, n_samples, sample_rate, pr)

    left = _sine(phases_l) * BINAURAL_AMP
    right = _sine(phases_r) * BINAURAL_AMP
    return np.stack([left, right], axis=1), _end_phase(phases_l), _end_phase(phases_r)


def _monaural_ramped(c0, c1, b0, b1, n_samples, sample_rate, pl, pr):
    c0, c1 = np.clip(c0, 100.0, 1000.0), np.clip(c1, 100.0, 1000.0)
    b0, b1 = np.clip(b0, 0.0, 40.0), np.clip(b1, 0.0, 40.0)

    carrier = _ramp_freq(c0, c1, n_samples)
    beat = _ramp_freq(b0, b1, n_samples)

    phases_l = _integrate_phases(carrier - beat * 0.5, n_samples, sample_rate, pl)
    phases_r = _integrate_phases(carrier + beat * 0.5, n_samples, sample_rate, pr)

    mono = (_sine(phases_l) + _sine(phases_r)) * MONAURAL_AMP
    return np.stack([mono, mono], axis=1), _end_phase(phases_l), _end_phase(phases_r)


def _isochronic_ramped(c0, c1, b0, b1, n_samples, sample_rate, pc, pb):
    c0, c1 = np.clip(c0, 100.0, 1000.0), np.clip(c1, 100.0, 1000.0)
    b0 = np.clip(max(b0, 0.1), 0.1, 40.0)
    b1 = np.clip(max(b1, 0.1), 0.1, 40.0)

    cf = _ramp_freq(c0, c1, n_samples)
    bf = _ramp_freq(b0, b1, n_samples)

    phases_c = _integrate_phases(cf, n_samples, sample_rate, pc)
    phases_b = _integrate_phases(bf, n_samples, sample_rate, pb)

    carrier = _sine(phases_c)
    gate = (0.5 - 0.5 * np.cos(phases_b)).astype(np.float32)
    mono = carrier * gate * ISOCHRONIC_AMP
    return np.stack([mono, mono], axis=1), _end_phase(phases_c), _end_phase(phases_b)


def generate_binaural_chunk(base_hz, beat_hz, duration_sec, sample_rate=44100,
                            phase_left=0.0, phase_right=0.0):
    """Generate binaural chunk (constant frequency — export/tests)."""
    n = _n_samples(duration_sec, sample_rate)
    return _binaural_ramped(base_hz, base_hz, beat_hz, beat_hz, n, sample_rate,
                            phase_left, phase_right)


def generate_binaural_chunk_ramped(c0, c1, b0, b1, n_samples, sample_rate,
                                   phase_left=0.0, phase_right=0.0):
    """Real-time chunk with frequency ramp across samples."""
    return _binaural_ramped(c0, c1, b0, b1, n_samples, sample_rate, phase_left, phase_right)


def generate_monaural_chunk(base_hz, beat_hz, duration_sec, sample_rate=44100,
                            phase_left=0.0, phase_right=0.0):
    n = _n_samples(duration_sec, sample_rate)
    return _monaural_ramped(base_hz, base_hz, beat_hz, beat_hz, n, sample_rate,
                            phase_left, phase_right)


def generate_monaural_chunk_ramped(c0, c1, b0, b1, n_samples, sample_rate,
                                   phase_left=0.0, phase_right=0.0):
    return _monaural_ramped(c0, c1, b0, b1, n_samples, sample_rate, phase_left, phase_right)


def generate_isochronic_chunk(carrier_hz, beat_hz, duration_sec, sample_rate=44100,
                               phase_carrier=0.0, phase_beat=0.0):
    n = _n_samples(duration_sec, sample_rate)
    return _isochronic_ramped(carrier_hz, carrier_hz, beat_hz, beat_hz, n, sample_rate,
                              phase_carrier, phase_beat)


def generate_isochronic_chunk_ramped(c0, c1, b0, b1, n_samples, sample_rate,
                                      phase_carrier=0.0, phase_beat=0.0):
    return _isochronic_ramped(c0, c1, b0, b1, n_samples, sample_rate, phase_carrier, phase_beat)


def generate_layered_binaural_chunk(base_start, base_end, beat_start, beat_end,
                                     n_samples, sample_rate=44100,
                                     phase_left=0.0, phase_right=0.0,
                                     n_layers=2, harmonic_phases=None):
    """Primary binaural pair + low-level harmonic bed (no extra beats)."""
    if harmonic_phases is None:
        harmonic_phases = [0.0, 0.0, 0.0]

    layer_ratios = [1.0, 1.5, 2.0]
    layer_amps = [0.82, 0.12, 0.06]
    n = min(n_layers, len(layer_ratios))
    total = sum(layer_amps[:n])

    primary, pl, pr = _binaural_ramped(
        base_start, base_end, beat_start, beat_end,
        n_samples, sample_rate, phase_left, phase_right)

    left = primary[:, 0] * (layer_amps[0] / BINAURAL_AMP)
    right = primary[:, 1] * (layer_amps[0] / BINAURAL_AMP)

    if n > 1:
        carrier = _ramp_freq(
            np.clip(base_start, 100.0, 1000.0),
            np.clip(base_end, 100.0, 1000.0),
            n_samples)
        for i in range(1, n):
            freq = np.clip(carrier * layer_ratios[i], 100.0, 4000.0)
            phases = _integrate_phases(freq, n_samples, sample_rate, harmonic_phases[i])
            tone = _sine(phases) * layer_amps[i]
            left += tone
            right += tone
            harmonic_phases[i] = _end_phase(phases)

    left /= total
    right /= total
    return np.stack([left, right], axis=1), pl, pr


def generate_layered_binaural_chunk_legacy(base_hz, beat_hz, duration_sec,
                                           sample_rate=44100, phase_left=0.0,
                                           phase_right=0.0, n_layers=2,
                                           harmonic_phases=None):
    n = _n_samples(duration_sec, sample_rate)
    return generate_layered_binaural_chunk(
        base_hz, base_hz, beat_hz, beat_hz, n, sample_rate,
        phase_left, phase_right, n_layers, harmonic_phases)


def generate_pink_noise(duration_sec, sample_rate=44100):
    n_samples = _n_samples(duration_sec, sample_rate)
    white = np.random.randn(n_samples).astype(np.float32)
    fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n_samples)
    freqs[0] = 1.0
    fft *= 1.0 / np.sqrt(freqs)
    fft[0] = 0.0
    pink = np.fft.irfft(fft, n=n_samples).astype(np.float32)
    peak = np.max(np.abs(pink))
    if peak > 1e-6:
        pink = pink / peak * 0.35
    return np.stack([pink, pink], axis=1)


def generate_white_noise(duration_sec, sample_rate=44100):
    n_samples = _n_samples(duration_sec, sample_rate)
    left = np.random.randn(n_samples).astype(np.float32) * 0.35
    right = np.random.randn(n_samples).astype(np.float32) * 0.35
    return np.stack([left, right], axis=1)


# ---------------------------------------------------------------------------
# Perception transforms — spatial / rhythmic modifiers applied after synthesis
# ---------------------------------------------------------------------------

PERCEPTION_MODES = ['standard', 'rotate', 'alternate', 'shimmer', 'breath']
PERCEPTION_LABELS = {
    'standard': 'Standard',
    'rotate': 'Rotating field',
    'alternate': 'Ear alternate',
    'shimmer': 'Shimmer',
    'breath': 'Breath sync',
}


def apply_perception(chunk, mode, beat_hz, sample_rate, state: dict):
    """
    Post-process a stereo chunk for expanded perceptual effects.

    Args:
        chunk: [n, 2] float32
        mode: one of PERCEPTION_MODES
        beat_hz: current beat frequency
        sample_rate: Hz
        state: mutable dict with 'rotation_phase', 'breath_phase'

    Returns:
        Modified chunk (same shape)
    """
    if mode == 'standard' or mode not in PERCEPTION_LABELS:
        return chunk

    n = chunk.shape[0]
    t = np.arange(n, dtype=np.float64) / sample_rate
    out = chunk.copy()

    if mode == 'rotate':
        # Slow rotation of interaural emphasis — "sound moves around head"
        rot_hz = min(0.15, max(0.04, beat_hz * 0.012))
        phase0 = state.get('rotation_phase', 0.0)
        pan = np.sin(2.0 * np.pi * rot_hz * t + phase0).astype(np.float32)
        state['rotation_phase'] = (phase0 + 2.0 * np.pi * rot_hz * (n / sample_rate)) % (2.0 * np.pi)
        # Crossfade L/R emphasis without changing pitch
        out[:, 0] = chunk[:, 0] * (0.88 + 0.12 * pan) + chunk[:, 1] * (0.04 * (1.0 - pan))
        out[:, 1] = chunk[:, 1] * (0.88 - 0.12 * pan) + chunk[:, 0] * (0.04 * (1.0 + pan))

    elif mode == 'alternate':
        # Pulse energy between ears at beat rate — strong spatial isochronic feel
        b = max(beat_hz, 0.5)
        phase0 = state.get('alt_phase', 0.0)
        gate = (0.5 - 0.5 * np.cos(2.0 * np.pi * b * t + phase0)).astype(np.float32)
        state['alt_phase'] = (phase0 + 2.0 * np.pi * b * (n / sample_rate)) % (2.0 * np.pi)
        mono = (chunk[:, 0] + chunk[:, 1]) * 0.5
        out[:, 0] = mono * gate
        out[:, 1] = mono * (1.0 - gate)

    elif mode == 'shimmer':
        # Gentle amplitude shimmer at half-beat rate — ethereal texture
        b = max(beat_hz, 0.5)
        phase0 = state.get('shimmer_phase', 0.0)
        am = (0.82 + 0.18 * np.sin(np.pi * b * t + phase0)).astype(np.float32)
        state['shimmer_phase'] = phase0 + np.pi * b * (n / sample_rate)
        out[:, 0] *= am
        out[:, 1] *= am

    elif mode == 'breath':
        # ~6 breaths/min amplitude swell — somatic entrainment
        breath_hz = 0.10
        phase0 = state.get('breath_phase', 0.0)
        swell = (0.55 + 0.45 * (0.5 - 0.5 * np.cos(2.0 * np.pi * breath_hz * t + phase0)))
        swell = swell.astype(np.float32)
        state['breath_phase'] = (phase0 + 2.0 * np.pi * breath_hz * (n / sample_rate)) % (2.0 * np.pi)
        out[:, 0] *= swell
        out[:, 1] *= swell

    return out


def cycle_perception_mode(current: str) -> str:
    modes = PERCEPTION_MODES
    if current not in modes:
        return modes[0]
    return modes[(modes.index(current) + 1) % len(modes)]

