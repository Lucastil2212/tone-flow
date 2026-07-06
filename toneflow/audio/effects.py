"""Audio effects: stereo reverb, noise, limiter."""

import numpy as np
from typing import Optional, Dict


# Reverb space presets — tuned for sustained sine/binaural tones
REVERB_PRESETS: Dict[str, dict] = {
    'off':   {'rt60': 0.0,  'wet': 0.0,  'damp': 0.0},
    'room':  {'rt60': 0.45, 'wet': 0.14, 'damp': 0.55},
    'chamber': {'rt60': 0.75, 'wet': 0.18, 'damp': 0.70},
    'cave':  {'rt60': 1.30, 'wet': 0.22, 'damp': 0.82},
}


class _CombFilter:
    """Single feedback comb with damping (one channel)."""

    __slots__ = ('delay', 'buffer', 'idx', 'gain', 'damp', 'filter_store')

    def __init__(self, delay_samples: int, gain: float, damp: float):
        self.delay = max(1, delay_samples)
        self.buffer = np.zeros(self.delay, dtype=np.float32)
        self.idx = 0
        self.gain = gain
        self.damp = damp
        self.filter_store = 0.0

    def process_sample(self, x: float) -> float:
        buf = self.buffer
        idx = self.idx
        delayed = buf[idx]

        # Low-pass in feedback path reduces metallic buildup on pure tones
        self.filter_store = delayed * (1.0 - self.damp) + self.filter_store * self.damp
        y = x + self.gain * self.filter_store
        buf[idx] = y
        self.idx = (idx + 1) % self.delay
        return y


class _AllpassFilter:
    """Schroeder allpass: y = -g*x + buf; buf = x + g*y"""

    __slots__ = ('delay', 'buffer', 'idx', 'gain')

    def __init__(self, delay_samples: int, gain: float = 0.5):
        self.delay = max(1, delay_samples)
        self.buffer = np.zeros(self.delay, dtype=np.float32)
        self.idx = 0
        self.gain = gain

    def process_sample(self, x: float) -> float:
        buf = self.buffer
        idx = self.idx
        delayed = buf[idx]
        y = -self.gain * x + delayed
        buf[idx] = x + self.gain * y
        self.idx = (idx + 1) % self.delay
        return y


class StereoReverb:
    """
    Stereo Schroeder reverb with **independent L/R delay lines**.

    Fixes the previous bug where both channels shared the same buffers,
    causing phase collapse and harsh metallic ringing on binaural tones.
    """

    # Prime-ish delays in ms (L slightly different from R for stereo width)
    _COMB_MS_L = [29.7, 37.1, 41.1, 43.7]
    _COMB_MS_R = [31.3, 38.9, 42.5, 44.9]
    _AP_MS = [5.2, 1.8, 3.7, 1.3]

    def __init__(self, sample_rate=44100, preset='room'):
        self.sample_rate = sample_rate
        self.preset_name = preset
        self.enabled = preset != 'off'
        self.wet = 0.15
        self.damp = 0.6
        self._combs_l: list = []
        self._combs_r: list = []
        self._ap_l: list = []
        self._ap_r: list = []
        self.apply_preset(preset)

    def apply_preset(self, preset: str):
        cfg = REVERB_PRESETS.get(preset, REVERB_PRESETS['room'])
        self.preset_name = preset
        self.enabled = preset != 'off' and cfg['wet'] > 0
        self.wet = cfg['wet']
        self.damp = cfg['damp']
        rt60 = cfg['rt60']
        sr = self.sample_rate

        self._combs_l = []
        self._combs_r = []
        for ms_l, ms_r in zip(self._COMB_MS_L, self._COMB_MS_R):
            d_l = int(ms_l * sr / 1000.0)
            d_r = int(ms_r * sr / 1000.0)
            g_l = 10 ** (-3.0 * d_l / sr / max(rt60, 0.01))
            g_r = 10 ** (-3.0 * d_r / sr / max(rt60, 0.01))
            self._combs_l.append(_CombFilter(d_l, g_l, self.damp))
            self._combs_r.append(_CombFilter(d_r, g_r, self.damp))

        self._ap_l = [_AllpassFilter(int(ms * sr / 1000.0), 0.5) for ms in self._AP_MS]
        self._ap_r = [_AllpassFilter(int(ms * sr / 1000.0), 0.5) for ms in self._AP_MS]

    def set_wet(self, wet: float):
        self.wet = float(np.clip(wet, 0.0, 0.45))

    def process(self, audio_chunk: np.ndarray) -> np.ndarray:
        if not self.enabled or self.wet <= 0:
            return audio_chunk

        n = audio_chunk.shape[0]
        out = np.empty_like(audio_chunk)
        wet = self.wet
        dry = 1.0 - wet

        for i in range(n):
            xl = float(audio_chunk[i, 0])
            xr = float(audio_chunk[i, 1])

            comb_l = sum(c.process_sample(xl) for c in self._combs_l) / len(self._combs_l)
            comb_r = sum(c.process_sample(xr) for c in self._combs_r) / len(self._combs_r)

            for ap in self._ap_l:
                comb_l = ap.process_sample(comb_l)
            for ap in self._ap_r:
                comb_r = ap.process_sample(comb_r)

            # Gentle cross-mix for enveloping stereo field
            wl, wr = comb_l, comb_r
            comb_l = 0.85 * wl + 0.15 * wr
            comb_r = 0.85 * wr + 0.15 * wl

            out[i, 0] = dry * xl + wet * comb_l
            out[i, 1] = dry * xr + wet * comb_r

        return out


class NoiseMixer:
    """Mix pink or white noise at a specified dBFS level."""

    def __init__(self, noise_generator, sample_rate=44100):
        self.noise_generator = noise_generator
        self.sample_rate = sample_rate
        self.level_dbfs = -24.0
        self.enabled = False
        self.noise_buffer = None
        self.noise_index = 0

    def set_level_dbfs(self, dbfs):
        self.level_dbfs = np.clip(dbfs, -36.0, -6.0)

    def enable(self, enabled):
        self.enabled = enabled

    def process(self, audio_chunk):
        if not self.enabled:
            return audio_chunk

        n_samples = audio_chunk.shape[0]
        if self.noise_buffer is None or (self.noise_index + n_samples) > len(self.noise_buffer):
            self.noise_buffer = self.noise_generator(1.0, self.sample_rate)
            self.noise_index = 0

        noise_chunk = self.noise_buffer[self.noise_index:self.noise_index + n_samples]
        self.noise_index += n_samples
        amplitude = 10 ** (self.level_dbfs / 20.0)
        return audio_chunk + amplitude * noise_chunk


class SoftLimiter:
    """Transparent limiter — only engages near full scale."""

    def __init__(self, threshold_db=-1.0):
        self.threshold = 10 ** (threshold_db / 20.0)

    def process(self, audio_chunk):
        peak = np.max(np.abs(audio_chunk))
        if peak <= self.threshold:
            return audio_chunk
        return audio_chunk * (self.threshold / peak)


class EffectsChain:
    """Composable effects: reverb → noise → limiter."""

    REVERB_CYCLE = ['off', 'room', 'chamber', 'cave']

    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.reverb: Optional[StereoReverb] = None
        self.reverb_preset = 'off'
        self.noise_mixer: Optional[NoiseMixer] = None
        self.limiter = SoftLimiter()

    def set_reverb(self, enabled, preset='room', wet=None):
        if enabled and preset != 'off':
            if self.reverb is None or self.reverb_preset != preset:
                self.reverb = StereoReverb(self.sample_rate, preset)
                self.reverb_preset = preset
            else:
                self.reverb.apply_preset(preset)
            if wet is not None:
                self.reverb.set_wet(wet)
            self.reverb.enabled = True
        else:
            self.reverb_preset = 'off'
            if self.reverb is not None:
                self.reverb.enabled = False

    def cycle_reverb_preset(self):
        """Cycle off → room → chamber → cave → off."""
        if self.reverb_preset not in self.REVERB_CYCLE:
            idx = 0
        else:
            idx = (self.REVERB_CYCLE.index(self.reverb_preset) + 1) % len(self.REVERB_CYCLE)
        preset = self.REVERB_CYCLE[idx]
        self.set_reverb(preset != 'off', preset=preset)
        return preset

    def set_reverb_wet(self, wet: float):
        if self.reverb is not None:
            self.reverb.set_wet(wet)

    def set_noise(self, enabled, noise_type='pink', level_dbfs=-24.0):
        if enabled:
            from . import osc
            gen = osc.generate_pink_noise if noise_type == 'pink' else osc.generate_white_noise
            self.noise_mixer = NoiseMixer(gen, self.sample_rate)
            self.noise_mixer.set_level_dbfs(level_dbfs)
            self.noise_mixer.enable(True)
        else:
            self.noise_mixer = None

    def process(self, audio_chunk):
        output = audio_chunk.copy()
        if self.reverb is not None and self.reverb.enabled:
            output = self.reverb.process(output)
        if self.noise_mixer is not None:
            output = self.noise_mixer.process(output)
        return self.limiter.process(output)
