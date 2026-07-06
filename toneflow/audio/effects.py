"""Audio effects chain: reverb, noise mixing, EQ."""

import numpy as np
from typing import Optional


class SchroederReverb:
    """
    Lightweight Schroeder reverb using comb and allpass filters.
    
    Classic architecture: 4 parallel comb filters → 2 series allpass filters.
    """
    
    def __init__(self, sample_rate=44100, reverb_time=0.5):
        """
        Initialize Schroeder reverb.
        
        Args:
            sample_rate: Sample rate in Hz
            reverb_time: Reverb decay time in seconds (0.3-0.7 typical)
        """
        self.sample_rate = sample_rate
        self.wet_dry = 0.35  # Default 35% wet
        
        # Comb filter delays (in samples) - prime numbers to avoid resonances
        # Typical room: 29.7, 37.1, 41.1, 43.7 ms
        comb_delays_ms = [29.7, 37.1, 41.1, 43.7]
        self.comb_delays = [int(ms * sample_rate / 1000.0) for ms in comb_delays_ms]
        
        # Allpass filter delays
        allpass_delays_ms = [5.0, 1.7]
        self.allpass_delays = [int(ms * sample_rate / 1000.0) for ms in allpass_delays_ms]
        
        # Initialize delay buffers
        self.comb_buffers = [np.zeros(d, dtype=np.float32) for d in self.comb_delays]
        self.comb_indices = [0] * len(self.comb_delays)
        
        self.allpass_buffers = [np.zeros(d, dtype=np.float32) for d in self.allpass_delays]
        self.allpass_indices = [0] * len(self.allpass_delays)
        
        # Calculate feedback coefficients for desired reverb time
        # g = 10^(-3*delay_time / reverb_time)
        self.comb_gains = []
        for delay in self.comb_delays:
            delay_sec = delay / sample_rate
            g = 10 ** (-3.0 * delay_sec / reverb_time)
            self.comb_gains.append(g)
        
        self.allpass_gain = 0.7  # Fixed for allpass
    
    def process(self, audio_chunk):
        """
        Process audio through reverb.
        
        Args:
            audio_chunk: Stereo array [n_samples, 2], float32
            
        Returns:
            Processed stereo array [n_samples, 2]
        """
        n_samples = audio_chunk.shape[0]
        output = np.zeros_like(audio_chunk)
        
        # Process each channel independently
        for ch in range(2):
            signal = audio_chunk[:, ch]
            
            # Comb filters (parallel, sum outputs)
            comb_sum = np.zeros(n_samples, dtype=np.float32)
            
            for i, (delay, gain) in enumerate(zip(self.comb_delays, self.comb_gains)):
                buffer = self.comb_buffers[i]
                idx = self.comb_indices[i]
                
                for s in range(n_samples):
                    # Read delayed sample
                    delayed = buffer[idx]
                    
                    # Comb filter: output = input + gain * delayed
                    out_sample = signal[s] + gain * delayed
                    
                    # Write to delay line
                    buffer[idx] = out_sample
                    
                    # Accumulate
                    comb_sum[s] += out_sample
                    
                    # Advance index
                    idx = (idx + 1) % delay
                
                self.comb_indices[i] = idx
            
            # Average comb outputs
            comb_sum /= len(self.comb_delays)
            
            # Allpass filters (series)
            allpass_out = comb_sum.copy()
            
            for i, delay in enumerate(self.allpass_delays):
                buffer = self.allpass_buffers[i]
                idx = self.allpass_indices[i]
                temp = np.zeros(n_samples, dtype=np.float32)
                
                for s in range(n_samples):
                    delayed = buffer[idx]
                    
                    # Allpass: output = -g*input + delayed + g*delayed
                    temp[s] = -self.allpass_gain * allpass_out[s] + delayed
                    buffer[idx] = allpass_out[s] + self.allpass_gain * delayed
                    
                    idx = (idx + 1) % delay
                
                allpass_out = temp
                self.allpass_indices[i] = idx
            
            # Mix wet/dry
            output[:, ch] = (1.0 - self.wet_dry) * signal + self.wet_dry * allpass_out
        
        return output
    
    def set_wet_dry(self, wet_dry):
        """Set wet/dry mix (0.0 = fully dry, 1.0 = fully wet)."""
        self.wet_dry = np.clip(wet_dry, 0.0, 1.0)


class NoiseMixer:
    """
    Mix pink or white noise at a specified dBFS level.
    """
    
    def __init__(self, noise_generator):
        """
        Initialize noise mixer.
        
        Args:
            noise_generator: Function that generates noise chunks
        """
        self.noise_generator = noise_generator
        self.level_dbfs = -20.0  # Default -20 dBFS
        self.enabled = False
        self.noise_buffer = None
        self.noise_index = 0
        self.sample_rate = 44100
    
    def set_level_dbfs(self, dbfs):
        """Set noise level in dBFS (-30 to -6 typical range)."""
        self.level_dbfs = np.clip(dbfs, -30.0, -6.0)
    
    def enable(self, enabled):
        """Enable or disable noise mixing."""
        self.enabled = enabled
    
    def process(self, audio_chunk):
        """
        Mix noise into audio chunk.
        
        Args:
            audio_chunk: Stereo array [n_samples, 2], float32
            
        Returns:
            Mixed stereo array [n_samples, 2]
        """
        if not self.enabled:
            return audio_chunk
        
        n_samples = audio_chunk.shape[0]
        
        # Generate noise if needed (keep a buffer for efficiency)
        if self.noise_buffer is None or (self.noise_index + n_samples) > len(self.noise_buffer):
            # Generate 1 second of noise
            self.noise_buffer = self.noise_generator(1.0, self.sample_rate)
            self.noise_index = 0
        
        # Extract chunk from noise buffer
        noise_chunk = self.noise_buffer[self.noise_index:self.noise_index + n_samples]
        self.noise_index += n_samples
        
        # Convert dBFS to linear amplitude
        # dBFS = 20*log10(amplitude/reference), reference = 1.0 for float
        amplitude = 10 ** (self.level_dbfs / 20.0)
        
        # Mix
        output = audio_chunk + amplitude * noise_chunk
        
        return output


class SoftLimiter:
    """Transparent limiter — only engages near full scale."""

    def __init__(self, threshold_db=-1.0):
        self.threshold = 10 ** (threshold_db / 20.0)

    def process(self, audio_chunk):
        peak = np.max(np.abs(audio_chunk))
        if peak <= self.threshold:
            return audio_chunk
        # Linear ceiling — no tanh coloration on sine waves
        return audio_chunk * (self.threshold / peak)


class EffectsChain:
    """
    Composable effects processing chain.
    """
    
    def __init__(self, sample_rate=44100):
        """Initialize effects chain."""
        self.sample_rate = sample_rate
        self.reverb: Optional[SchroederReverb] = None
        self.noise_mixer: Optional[NoiseMixer] = None
        self.limiter = SoftLimiter()
        
    def set_reverb(self, enabled, wet_dry=0.35):
        """Enable/configure reverb."""
        if enabled:
            if self.reverb is None:
                self.reverb = SchroederReverb(self.sample_rate)
            self.reverb.set_wet_dry(wet_dry)
        else:
            self.reverb = None
    
    def set_noise(self, enabled, noise_type='pink', level_dbfs=-20.0):
        """Enable/configure noise mixing."""
        if enabled:
            from . import osc
            if noise_type == 'pink':
                generator = osc.generate_pink_noise
            else:
                generator = osc.generate_white_noise
            
            self.noise_mixer = NoiseMixer(generator)
            self.noise_mixer.set_level_dbfs(level_dbfs)
            self.noise_mixer.enable(True)
        else:
            self.noise_mixer = None
    
    def process(self, audio_chunk):
        """
        Process audio through full effects chain.
        
        Order: reverb → noise → limiter
        
        Args:
            audio_chunk: Stereo array [n_samples, 2], float32
            
        Returns:
            Processed stereo array [n_samples, 2]
        """
        output = audio_chunk.copy()
        
        # Apply reverb
        if self.reverb is not None:
            output = self.reverb.process(output)
        
        # Mix noise
        if self.noise_mixer is not None:
            output = self.noise_mixer.process(output)
        
        # Always apply limiter last
        output = self.limiter.process(output)
        
        return output

