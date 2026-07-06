"""Real-time audio engine — clean synthesis with reliable buffer delivery."""

import numpy as np
import pygame
from typing import Optional
from . import osc
from .effects import EffectsChain


BRAINWAVE_BANDS = [
    (0.0,  4.0,  "Delta",  "deep sleep / unconscious",  (30,  60, 200)),
    (4.0,  8.0,  "Theta",  "deep meditation / creativity", (120, 40, 200)),
    (8.0,  12.0, "Alpha",  "relaxed alertness",          (40, 180, 100)),
    (12.0, 30.0, "Beta",   "focused attention",          (220, 180, 0)),
    (30.0, 100.0,"Gamma",  "peak cognition",             (255, 255, 255)),
]


def get_brainwave_band(beat_hz):
    for low, high, name, desc, colour in BRAINWAVE_BANDS:
        if low <= beat_hz < high:
            return name, desc, colour
    return "Gamma", "peak cognition", (255, 255, 255)


class AudioEngine:
    """
    Real-time binaural/isochronic/monaural engine.

    Design choices for clean output:
    - 2048-sample chunks (~46 ms) — safe at 60 FPS (needs ~22 chunks/s, supplies 60)
    - Per-sample frequency ramp — no stepped warble between chunks
    - Phase integration — no crossfade needed (crossfade caused doubling artifacts)
    - No limiter on dry signal — only when effects push levels up
    """

    CHUNK_SAMPLES = 2048

    def __init__(self, sample_rate=44100, buffer_size=None):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size or self.CHUNK_SAMPLES
        self.chunk_duration = self.buffer_size / sample_rate

        self.carrier_hz = 200.0
        self.beat_hz = 10.0
        self.target_carrier_hz = 200.0
        self.target_beat_hz = 10.0

        self.mode = 'binaural'
        self.isochronic_mode = False
        self.harmonic_layers = 1
        self.harmonic_phases = [0.0, 0.0, 0.0]

        # Perception mode — spatial/rhythmic post-processing
        self.perception_mode = 'standard'
        self._perception_state = {
            'rotation_phase': 0.0,
            'alt_phase': 0.0,
            'shimmer_phase': 0.0,
            'breath_phase': 0.0,
        }

        # ~150 ms smoothing — stable tone, smooth tuning
        self.smooth_alpha = 1.0 - np.exp(-self.chunk_duration / 0.150)

        pygame.mixer.set_num_channels(1)
        self.effects = EffectsChain(sample_rate)

        self.is_playing = False
        self.session_time = 0.0
        self.session_duration = 900.0
        self.ramp_duration = 30.0

        self.current_rms = 0.0
        self.spl_calibration_offset = 0.0

        self.phase_left = 0.0
        self.phase_right = 0.0

        self.last_chunk: Optional[np.ndarray] = None
        self.master_volume = 0.15
        self.channel: Optional[pygame.mixer.Channel] = None

        # Stats
        self._underruns = 0

    def set_parameters(self, carrier_hz, beat_hz):
        self.target_carrier_hz = np.clip(carrier_hz, 100.0, 1000.0)
        self.target_beat_hz = np.clip(beat_hz, 0.0, 40.0)

    def snap_parameters(self):
        """Instantly lock to targets (call when tuning ends)."""
        self.carrier_hz = self.target_carrier_hz
        self.beat_hz = self.target_beat_hz

    def set_mode(self, mode):
        if mode in ('binaural', 'monaural'):
            self.mode = mode

    def set_perception_mode(self, mode):
        if mode in osc.PERCEPTION_MODES:
            self.perception_mode = mode

    def cycle_perception_mode(self):
        self.perception_mode = osc.cycle_perception_mode(self.perception_mode)
        return self.perception_mode

    def get_reverb_info(self):
        """Return (preset_name, wet) for UI."""
        fx = self.effects
        if fx.reverb is None or not fx.reverb.enabled:
            return 'off', 0.0
        return fx.reverb_preset, fx.reverb.wet

    def cycle_reverb(self):
        return self.effects.cycle_reverb_preset()

    def set_reverb_wet(self, wet):
        self.effects.set_reverb_wet(wet)

    def set_volume(self, volume):
        self.master_volume = np.clip(volume, 0.0, 1.0)

    def adjust_volume(self, delta):
        self.master_volume = np.clip(self.master_volume + delta, 0.0, 1.0)

    def start_session(self, duration_min):
        self.is_playing = True
        self.session_time = 0.0
        self.session_duration = (duration_min * 60.0) if duration_min is not None else float('inf')
        if self.channel is None:
            self.channel = pygame.mixer.find_channel()

    def stop_session(self):
        self.is_playing = False
        if self.channel is not None:
            self.channel.stop()

    def update(self, dt):
        """Keep the mixer fed — may queue up to 2 chunks per call."""
        if self.channel is None:
            self.channel = pygame.mixer.Channel(0)

        if self.is_playing:
            self.session_time += dt
            if self.session_time >= self.session_duration:
                self.stop_session()

        chunks_this_frame = 0
        max_per_frame = 3

        while chunks_this_frame < max_per_frame:
            if not self.channel.get_busy():
                self._underruns += 1
                self._queue_chunk(play=True)
                chunks_this_frame += 1
            elif self.channel.get_queue() is None:
                self._queue_chunk(play=False)
                chunks_this_frame += 1
            else:
                break

    def _queue_chunk(self, play=False):
        chunk = self._generate_chunk()
        chunk_int16 = np.clip(chunk * 32767.0, -32768, 32767).astype(np.int16)
        sound = pygame.sndarray.make_sound(chunk_int16)
        if play:
            self.channel.play(sound)
        else:
            self.channel.queue(sound)

    def _generate_chunk(self):
        n = self.buffer_size

        # Frequency at start and end of this chunk (ramped smoothly within chunk)
        c0 = self.carrier_hz
        b0 = self.beat_hz
        self.carrier_hz += self.smooth_alpha * (self.target_carrier_hz - self.carrier_hz)
        self.beat_hz += self.smooth_alpha * (self.target_beat_hz - self.beat_hz)
        c1 = self.carrier_hz
        b1 = self.beat_hz

        if self.isochronic_mode:
            chunk, self.phase_left, self.phase_right = osc.generate_isochronic_chunk_ramped(
                c0, c1, b0, b1, n, self.sample_rate, self.phase_left, self.phase_right)
        elif self.harmonic_layers > 1:
            chunk, self.phase_left, self.phase_right = osc.generate_layered_binaural_chunk(
                c0, c1, b0, b1, n, self.sample_rate,
                self.phase_left, self.phase_right,
                n_layers=self.harmonic_layers,
                harmonic_phases=self.harmonic_phases)
        elif self.mode == 'binaural':
            chunk, self.phase_left, self.phase_right = osc.generate_binaural_chunk_ramped(
                c0, c1, b0, b1, n, self.sample_rate, self.phase_left, self.phase_right)
        else:
            chunk, self.phase_left, self.phase_right = osc.generate_monaural_chunk_ramped(
                c0, c1, b0, b1, n, self.sample_rate, self.phase_left, self.phase_right)

        chunk = osc.apply_perception(
            chunk, self.perception_mode, self.beat_hz,
            self.sample_rate, self._perception_state)

        chunk = self._apply_ramp(chunk)
        chunk = self.effects.process(chunk)
        chunk = chunk * self.master_volume

        self.current_rms = float(np.sqrt(np.mean(chunk ** 2)))
        self.last_chunk = chunk.copy()
        return chunk

    def _apply_ramp(self, chunk):
        if not self.is_playing:
            return chunk

        n = chunk.shape[0]
        env = np.ones(n, dtype=np.float32)
        dt_sample = 1.0 / self.sample_rate

        if self.session_time < self.ramp_duration:
            t0 = self.session_time - self.chunk_duration
            for i in range(n):
                t = t0 + i * dt_sample
                if t < self.ramp_duration:
                    env[i] = max(0.0, t / self.ramp_duration)

        if self.session_duration != float('inf'):
            for i in range(n):
                t = self.session_time - self.chunk_duration + i * dt_sample
                remaining = self.session_duration - t
                if remaining < self.ramp_duration:
                    env[i] *= max(0.0, remaining / self.ramp_duration)

        return chunk * env[:, np.newaxis]

    def get_last_chunk(self):
        return self.last_chunk

    def get_current_spl_dbfs(self):
        if self.current_rms < 1e-10:
            return -100.0
        return 20.0 * np.log10(self.current_rms)

    def get_current_spl_dba(self):
        return self.get_current_spl_dbfs() + self.spl_calibration_offset

    def get_spl_badge(self):
        dba = self.get_current_spl_dba()
        if dba < 75.0:
            return 'green'
        if dba < 80.0:
            return 'amber'
        return 'red'

    def get_brainwave_state(self):
        return get_brainwave_band(self.beat_hz)

    def set_spl_calibration(self, reference_dba):
        self.spl_calibration_offset = reference_dba - self.get_current_spl_dbfs()

    def get_session_progress(self):
        total = None if self.session_duration == float('inf') else self.session_duration
        is_ramp_in = self.session_time < self.ramp_duration
        is_ramp_out = (total is not None and
                       (total - self.session_time) < self.ramp_duration)
        return self.session_time, total, is_ramp_in, is_ramp_out
