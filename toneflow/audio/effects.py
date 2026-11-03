"""Audio effects: stereo reverb, noise, limiter — optimized for real-time."""

import numpy as np
from typing import Optional, Dict
from scipy import signal as spsig


# Reverb space presets — tuned for sustained sine/binaural tones
REVERB_PRESETS: Dict[str, dict] = {
    'off':     {'rt60': 0.0,  'wet': 0.0,  'damp': 0.0},
    'room':    {'rt60': 0.45, 'wet': 0.14, 'damp': 0.55},
    'chamber': {'rt60': 0.75, 'wet': 0.18, 'damp': 0.70},
    'cave':    {'rt60': 1.30, 'wet': 0.22, 'damp': 0.82},
}


class StereoReverb:
    """
    Stereo Schroeder-style reverb using SciPy IIR filters (C-backed).

    Previous per-sample Python loops caused mixer underruns / crackling.
    Comb + allpass sections are now processed with scipy.signal.lfilter
    so a 2048-sample chunk stays well under real-time budget.
    """

    _COMB_MS_L = [29.7, 37.1, 41.1, 43.7]
    _COMB_MS_R = [31.3, 38.9, 42.5, 44.9]
    _AP_MS_L = [5.2, 1.8, 3.7, 1.3]
    _AP_MS_R = [5.5, 1.9, 4.1, 1.5]

    def __init__(self, sample_rate=44100, preset='room'):
        self.sample_rate = sample_rate
        self.preset_name = preset
        self.enabled = preset != 'off'
        self.wet = 0.15
        self.damp = 0.6
        # Each entry: (b, a, zi) for lfilter
        self._combs_l = []
        self._combs_r = []
        self._ap_l = []
        self._ap_r = []
        self.apply_preset(preset)

    @staticmethod
    def _comb_ba(delay: int, gain: float, damp: float):
        """
        Feedback comb with one-pole damping in the feedback path.

        Approx: y = x + g * lp(y_delayed)
        Implemented as cascade of delay feedback + light LP on output.
        """
        delay = max(1, delay)
        # Primary feedback delay: y[n] = x[n] + g*(1-damp)*y[n-D]
        # Damping reduces high-frequency buildup (important for pure tones).
        g_eff = float(gain) * (1.0 - 0.35 * damp)
        b = np.zeros(delay + 1, dtype=np.float64)
        a = np.zeros(delay + 1, dtype=np.float64)
        b[0] = 1.0
        a[0] = 1.0
        a[delay] = -g_eff
        return b, a

    @staticmethod
    def _allpass_ba(delay: int, gain: float = 0.5):
        """Schroeder allpass: y[n] = -g*x[n] + x[n-D] + g*y[n-D]."""
        delay = max(1, delay)
        g = float(gain)
        b = np.zeros(delay + 1, dtype=np.float64)
        a = np.zeros(delay + 1, dtype=np.float64)
        b[0] = -g
        b[delay] = 1.0
        a[0] = 1.0
        a[delay] = -g
        return b, a

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
            d_l = max(1, int(ms_l * sr / 1000.0))
            d_r = max(1, int(ms_r * sr / 1000.0))
            g_l = 10 ** (-3.0 * d_l / sr / max(rt60, 0.01))
            g_r = 10 ** (-3.0 * d_r / sr / max(rt60, 0.01))
            b_l, a_l = self._comb_ba(d_l, g_l, self.damp)
            b_r, a_r = self._comb_ba(d_r, g_r, self.damp)
            zi_l = spsig.lfilter_zi(b_l, a_l) * 0.0
            zi_r = spsig.lfilter_zi(b_r, a_r) * 0.0
            self._combs_l.append([b_l, a_l, zi_l])
            self._combs_r.append([b_r, a_r, zi_r])

        self._ap_l = []
        self._ap_r = []
        for ms_l, ms_r in zip(self._AP_MS_L, self._AP_MS_R):
            d_l = max(1, int(ms_l * sr / 1000.0))
            d_r = max(1, int(ms_r * sr / 1000.0))
            b_l, a_l = self._allpass_ba(d_l, 0.5)
            b_r, a_r = self._allpass_ba(d_r, 0.5)
            self._ap_l.append([b_l, a_l, spsig.lfilter_zi(b_l, a_l) * 0.0])
            self._ap_r.append([b_r, a_r, spsig.lfilter_zi(b_r, a_r) * 0.0])

    def set_wet(self, wet: float):
        self.wet = float(np.clip(wet, 0.0, 0.45))

    @staticmethod
    def _run_filters(x: np.ndarray, sections: list) -> np.ndarray:
        y = x.astype(np.float64, copy=False)
        for sec in sections:
            b, a, zi = sec
            y, zo = spsig.lfilter(b, a, y, zi=zi)
            sec[2] = zo
        return y

    def process(self, audio_chunk: np.ndarray) -> np.ndarray:
        if not self.enabled or self.wet <= 0:
            return audio_chunk

        xl = audio_chunk[:, 0]
        xr = audio_chunk[:, 1]

        # Parallel combs, then series allpasses
        comb_l = np.zeros(xl.shape[0], dtype=np.float64)
        comb_r = np.zeros(xr.shape[0], dtype=np.float64)
        n_combs = len(self._combs_l)
        for i in range(n_combs):
            b, a, zi = self._combs_l[i]
            yl, zo = spsig.lfilter(b, a, xl.astype(np.float64), zi=zi)
            self._combs_l[i][2] = zo
            comb_l += yl
            b, a, zi = self._combs_r[i]
            yr, zo = spsig.lfilter(b, a, xr.astype(np.float64), zi=zi)
            self._combs_r[i][2] = zo
            comb_r += yr

        comb_l /= n_combs
        comb_r /= n_combs

        comb_l = self._run_filters(comb_l, self._ap_l)
        comb_r = self._run_filters(comb_r, self._ap_r)

        # Gentle cross-mix for enveloping stereo field
        wl, wr = comb_l, comb_r
        comb_l = 0.85 * wl + 0.15 * wr
        comb_r = 0.85 * wr + 0.15 * wl

        wet = self.wet
        dry = 1.0 - wet
        out = np.empty_like(audio_chunk)
        out[:, 0] = (dry * xl + wet * comb_l).astype(np.float32)
        out[:, 1] = (dry * xr + wet * comb_r).astype(np.float32)
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
            self.noise_buffer = self.noise_generator(2.0, self.sample_rate)
            self.noise_index = 0

        noise_chunk = self.noise_buffer[self.noise_index:self.noise_index + n_samples]
        self.noise_index += n_samples
        amplitude = 10 ** (self.level_dbfs / 20.0)
        return audio_chunk + amplitude * noise_chunk


class SoftLimiter:
    """
    Transparent peak limiter — only engages near full scale.

    Attack is instantaneous on the current chunk (prevents hard clips /
    crackling), release is smoothed so gain recovery isn't zipper-noisy.
    """

    def __init__(self, threshold_db=-1.5):
        self.threshold = 10 ** (threshold_db / 20.0)
        self._gain = 1.0
        self._release = 0.12  # fraction toward 1.0 per chunk when below ceiling

    def process(self, audio_chunk):
        peak = float(np.max(np.abs(audio_chunk)))
        if peak < 1e-12:
            return audio_chunk

        # Instant ceiling for this chunk — never let peaks through
        if peak > self.threshold:
            needed = self.threshold / peak
            self._gain = min(self._gain, needed)
        else:
            # Smooth release when headroom returns
            self._gain += self._release * (1.0 - self._gain)

        if self._gain >= 0.999:
            self._gain = 1.0
            return audio_chunk
        return (audio_chunk * np.float32(self._gain)).astype(np.float32)


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
        output = audio_chunk
        if self.reverb is not None and self.reverb.enabled:
            output = self.reverb.process(output)
        if self.noise_mixer is not None:
            output = self.noise_mixer.process(output)
        return self.limiter.process(output)
