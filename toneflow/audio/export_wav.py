"""Offline WAV export renderer."""

import numpy as np
from scipy.io import wavfile
from typing import Dict, Any
from . import osc
from .effects import EffectsChain


def export_wav(
    carrier_hz: float,
    beat_hz: float,
    mode: str,
    duration_min: float,
    output_path: str,
    effects_config: Dict[str, Any],
    sample_rate: int = 44100
):
    """
    Export a binaural/monaural beat session to WAV file.
    
    Renders the entire session offline with effects.
    
    Args:
        carrier_hz: Carrier frequency (20-1000 Hz)
        beat_hz: Beat frequency (0-40 Hz)
        mode: 'binaural' or 'monaural'
        duration_min: Duration in minutes
        output_path: Output file path (.wav)
        effects_config: Dict with 'reverb', 'noise' settings
        sample_rate: Sample rate (default 44100 Hz)
    """
    duration_sec = duration_min * 60.0
    ramp_duration = 30.0  # 30 second ramp-in/out
    
    # Clamp parameters
    from .osc import CARRIER_MIN_HZ, CARRIER_MAX_HZ
    carrier_hz = np.clip(carrier_hz, CARRIER_MIN_HZ, CARRIER_MAX_HZ)
    beat_hz = np.clip(beat_hz, 0.0, 40.0)
    
    # Generate full session audio (with phase continuity from 0)
    if mode == 'binaural':
        audio, _, _ = osc.generate_binaural_chunk(carrier_hz, beat_hz, duration_sec, sample_rate)
    elif mode == 'monaural':
        audio, _, _ = osc.generate_monaural_chunk(carrier_hz, beat_hz, duration_sec, sample_rate)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    # Apply ramp-in/out envelope
    n_samples = audio.shape[0]
    envelope = np.ones(n_samples, dtype=np.float32)
    
    # Limit ramp to not exceed half the duration
    max_ramp_samples = n_samples // 2
    ramp_samples = min(int(ramp_duration * sample_rate), max_ramp_samples)
    
    # Ramp-in
    if ramp_samples > 0:
        ramp_in = np.linspace(0.0, 1.0, ramp_samples, dtype=np.float32)
        envelope[:ramp_samples] = ramp_in
    
    # Ramp-out
    if ramp_samples > 0:
        ramp_out = np.linspace(1.0, 0.0, ramp_samples, dtype=np.float32)
        envelope[-ramp_samples:] = ramp_out
    
    # Apply envelope to both channels
    audio = audio * envelope[:, np.newaxis]
    
    # Process in chunks through effects (to avoid memory issues)
    effects = EffectsChain(sample_rate)
    
    # Configure effects from config dict
    if effects_config.get('reverb', {}).get('enabled', False):
        preset = effects_config['reverb'].get('preset', 'room')
        wet = effects_config['reverb'].get('wet_dry', 0.18)
        effects.set_reverb(True, preset=preset, wet=wet)
    
    if effects_config.get('noise', {}).get('enabled', False):
        noise_type = effects_config['noise'].get('type', 'pink')
        level_dbfs = effects_config['noise'].get('level_dbfs', -20.0)
        effects.set_noise(True, noise_type, level_dbfs)
    
    # Process in 1-second chunks
    chunk_size = sample_rate
    n_chunks = (n_samples + chunk_size - 1) // chunk_size
    
    output_audio = np.zeros_like(audio)
    
    for i in range(n_chunks):
        start = i * chunk_size
        end = min((i + 1) * chunk_size, n_samples)
        chunk = audio[start:end]
        processed_chunk = effects.process(chunk)
        output_audio[start:end] = processed_chunk
    
    # Convert to int16 for WAV
    output_int16 = (output_audio * 32767.0).astype(np.int16)
    
    # Write WAV file
    wavfile.write(output_path, sample_rate, output_int16)
    
    return output_path

