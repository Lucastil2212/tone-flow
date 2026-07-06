"""Real-time audio meters: waveform, spectrum, and level displays."""

import numpy as np
import pygame
from typing import Optional


class WaveformMeter:
    """
    Real-time waveform display (oscilloscope-style).
    
    Shows last 100ms of audio with L/R channels.
    """
    
    def __init__(self, width, height, duration_ms=100, sample_rate=44100):
        """
        Initialize waveform meter.
        
        Args:
            width: Display width in pixels
            height: Display height in pixels
            duration_ms: Buffer duration in milliseconds
            sample_rate: Audio sample rate
        """
        self.width = width
        self.height = height
        self.duration_ms = duration_ms
        self.sample_rate = sample_rate
        
        # Rolling buffer size
        self.buffer_size = int(sample_rate * duration_ms / 1000)
        self.buffer_l = np.zeros(self.buffer_size, dtype=np.float32)
        self.buffer_r = np.zeros(self.buffer_size, dtype=np.float32)
        self.buffer_pos = 0
        
        # Colors
        self.color_l = (0, 255, 255)  # Cyan for left
        self.color_r = (255, 0, 255)  # Magenta for right
        self.color_grid = (40, 40, 50)
        self.color_bg = (10, 10, 15)
    
    def update(self, chunk_stereo):
        """
        Update buffer with new audio chunk.
        
        Args:
            chunk_stereo: Stereo array [n_samples, 2]
        """
        if chunk_stereo is None:
            return
        
        n_samples = min(len(chunk_stereo), self.buffer_size)
        
        # Roll buffer and append new samples
        self.buffer_l = np.roll(self.buffer_l, -n_samples)
        self.buffer_r = np.roll(self.buffer_r, -n_samples)
        
        self.buffer_l[-n_samples:] = chunk_stereo[:n_samples, 0]
        self.buffer_r[-n_samples:] = chunk_stereo[:n_samples, 1]
    
    def render(self, surface, x, y):
        """
        Render waveform to surface.
        
        Args:
            surface: Pygame surface
            x, y: Top-left position
        """
        # Background
        pygame.draw.rect(surface, self.color_bg, (x, y, self.width, self.height))
        
        # Grid lines (±1.0, 0.0)
        mid_y = y + self.height // 2
        pygame.draw.line(surface, self.color_grid, (x, mid_y), (x + self.width, mid_y), 1)
        pygame.draw.line(surface, self.color_grid, (x, y + self.height // 4), 
                        (x + self.width, y + self.height // 4), 1)
        pygame.draw.line(surface, self.color_grid, (x, y + 3 * self.height // 4), 
                        (x + self.width, y + 3 * self.height // 4), 1)
        
        # Decimate buffer to screen width
        decimation = max(1, self.buffer_size // self.width)
        decimated_l = self.buffer_l[::decimation]
        decimated_r = self.buffer_r[::decimation]
        
        # Draw left channel
        self._draw_waveform(surface, x, y, decimated_l, self.color_l)
        
        # Draw right channel
        self._draw_waveform(surface, x, y, decimated_r, self.color_r)
        
        # Border
        pygame.draw.rect(surface, (60, 60, 70), (x, y, self.width, self.height), 1)
    
    def _draw_waveform(self, surface, x_offset, y_offset, data, color):
        """Draw a single channel waveform."""
        if len(data) < 2:
            return
        
        points = []
        mid_y = y_offset + self.height // 2
        
        for i, sample in enumerate(data):
            px = x_offset + int(i * self.width / len(data))
            # Map [-1, 1] to display height
            py = mid_y - int(sample * (self.height // 2 - 2))
            py = max(y_offset, min(y_offset + self.height, py))
            points.append((px, py))
        
        if len(points) >= 2:
            pygame.draw.lines(surface, color, False, points, 1)


class SpectrumMeter:
    """
    FFT-based spectrum analyzer.
    
    Shows frequency content from 20-2000 Hz.
    """
    
    def __init__(self, width, height, sample_rate=44100, fft_size=1024):
        """
        Initialize spectrum analyzer.
        
        Args:
            width: Display width in pixels
            height: Display height in pixels
            sample_rate: Audio sample rate
            fft_size: FFT window size (power of 2)
        """
        self.width = width
        self.height = height
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        
        # Frequency range to display
        self.freq_min = 20.0
        self.freq_max = 2000.0
        
        # Magnitude range (dB)
        self.db_min = -60.0
        self.db_max = 0.0
        
        # Number of display bars
        self.n_bars = 60
        
        # Peak hold
        self.peak_hold = np.zeros(self.n_bars)
        self.peak_decay = 0.95  # Per frame
        
        # Colors
        self.color_bar = (80, 200, 255)
        self.color_peak = (255, 255, 100)
        self.color_bg = (10, 10, 15)
        self.color_grid = (40, 40, 50)
        
        # Hann window for FFT
        self.window = np.hanning(fft_size)
        
        # Initialize bar heights (prevents AttributeError on first render)
        self.bar_heights = np.zeros(self.n_bars)
        
        # Update counter (don't update every frame)
        self.update_counter = 0
        self.update_rate = 2  # Update every 2 frames
    
    def update(self, chunk_stereo):
        """
        Update spectrum from audio chunk.
        
        Args:
            chunk_stereo: Stereo array [n_samples, 2]
        """
        if chunk_stereo is None:
            return
        
        self.update_counter += 1
        if self.update_counter % self.update_rate != 0:
            return  # Skip this frame
        
        # Mix to mono for spectrum
        mono = np.mean(chunk_stereo, axis=1)
        
        # Pad or truncate to FFT size
        if len(mono) < self.fft_size:
            mono = np.pad(mono, (0, self.fft_size - len(mono)))
        else:
            mono = mono[:self.fft_size]
        
        # Apply window and compute FFT
        windowed = mono * self.window
        fft_result = np.fft.rfft(windowed)
        magnitude = np.abs(fft_result)
        
        # Convert to dB
        magnitude_db = 20 * np.log10(magnitude + 1e-10)
        
        # Frequency bins
        freqs = np.fft.rfftfreq(self.fft_size, 1.0 / self.sample_rate)
        
        # Map to logarithmic display bars
        log_freqs = np.logspace(np.log10(self.freq_min), np.log10(self.freq_max), self.n_bars + 1)
        
        bar_values = np.zeros(self.n_bars)
        for i in range(self.n_bars):
            # Find FFT bins in this frequency range
            f_low = log_freqs[i]
            f_high = log_freqs[i + 1]
            mask = (freqs >= f_low) & (freqs < f_high)
            
            if np.any(mask):
                # Take max magnitude in this range
                bar_values[i] = np.max(magnitude_db[mask])
        
        # Normalize to [0, 1]
        self.bar_heights = np.clip((bar_values - self.db_min) / (self.db_max - self.db_min), 0.0, 1.0)
        
        # Update peak hold
        self.peak_hold = np.maximum(self.peak_hold * self.peak_decay, self.bar_heights)
    
    def render(self, surface, x, y):
        """
        Render spectrum analyzer to surface.
        
        Args:
            surface: Pygame surface
            x, y: Top-left position
        """
        # Background
        pygame.draw.rect(surface, self.color_bg, (x, y, self.width, self.height))
        
        # Grid lines (every -20 dB)
        for db in [-20, -40]:
            grid_y = y + int((1.0 - (db - self.db_min) / (self.db_max - self.db_min)) * self.height)
            pygame.draw.line(surface, self.color_grid, (x, grid_y), (x + self.width, grid_y), 1)
        
        # Draw bars
        bar_width = max(1, (self.width - self.n_bars) // self.n_bars)
        bar_spacing = 1
        
        for i in range(self.n_bars):
            bar_x = x + i * (bar_width + bar_spacing)
            
            # Bar height
            bar_h = int(self.bar_heights[i] * self.height) if hasattr(self, 'bar_heights') else 0
            bar_y = y + self.height - bar_h
            
            # Draw bar with gradient (green -> yellow -> red)
            if self.bar_heights[i] > 0.8:
                color = (255, 80, 80)  # Red
            elif self.bar_heights[i] > 0.5:
                color = (255, 200, 0)  # Yellow
            else:
                color = self.color_bar  # Cyan/blue
            
            if bar_h > 0:
                pygame.draw.rect(surface, color, (bar_x, bar_y, bar_width, bar_h))
            
            # Peak hold indicator
            peak_h = int(self.peak_hold[i] * self.height)
            peak_y = y + self.height - peak_h
            if peak_h > 0:
                pygame.draw.line(surface, self.color_peak, (bar_x, peak_y), 
                               (bar_x + bar_width, peak_y), 2)
        
        # Border
        pygame.draw.rect(surface, (60, 60, 70), (x, y, self.width, self.height), 1)


class LevelMeter:
    """
    Stereo RMS/peak level meter with dBFS scale.
    """
    
    def __init__(self, width, height):
        """
        Initialize level meter.
        
        Args:
            width: Display width in pixels (for 2 bars side-by-side)
            height: Display height in pixels
        """
        self.width = width
        self.height = height
        
        # dB range
        self.db_min = -60.0
        self.db_max = 0.0
        
        # Current levels
        self.rms_l = -60.0
        self.rms_r = -60.0
        self.peak_l = -60.0
        self.peak_r = -60.0
        
        # Peak hold
        self.peak_hold_l = -60.0
        self.peak_hold_r = -60.0
        self.peak_hold_time = 0.0
        self.peak_hold_duration = 0.3  # 300ms
        
        # Colors
        self.color_green = (80, 255, 120)
        self.color_yellow = (255, 200, 0)
        self.color_red = (255, 80, 80)
        self.color_peak = (255, 255, 255)
        self.color_bg = (10, 10, 15)
        self.color_border = (60, 60, 70)
        
        # Font for labels
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 10)
    
    def update(self, chunk_stereo, dt):
        """
        Update levels from audio chunk.
        
        Args:
            chunk_stereo: Stereo array [n_samples, 2]
            dt: Time delta for peak hold decay
        """
        if chunk_stereo is None:
            return
        
        # Calculate RMS for each channel
        rms_l = np.sqrt(np.mean(chunk_stereo[:, 0] ** 2))
        rms_r = np.sqrt(np.mean(chunk_stereo[:, 1] ** 2))
        
        # Convert to dB
        self.rms_l = 20 * np.log10(rms_l + 1e-10)
        self.rms_r = 20 * np.log10(rms_r + 1e-10)
        
        # Calculate peak
        peak_l = np.max(np.abs(chunk_stereo[:, 0]))
        peak_r = np.max(np.abs(chunk_stereo[:, 1]))
        
        self.peak_l = 20 * np.log10(peak_l + 1e-10)
        self.peak_r = 20 * np.log10(peak_r + 1e-10)
        
        # Update peak hold
        if self.peak_l > self.peak_hold_l:
            self.peak_hold_l = self.peak_l
            self.peak_hold_time = 0.0
        if self.peak_r > self.peak_hold_r:
            self.peak_hold_r = self.peak_r
            self.peak_hold_time = 0.0
        
        # Decay peak hold
        self.peak_hold_time += dt
        if self.peak_hold_time > self.peak_hold_duration:
            decay_rate = 40.0  # dB per second
            self.peak_hold_l -= decay_rate * dt
            self.peak_hold_r -= decay_rate * dt
    
    def render(self, surface, x, y):
        """
        Render level meters to surface.
        
        Args:
            surface: Pygame surface
            x, y: Top-left position
        """
        bar_width = self.width // 2 - 2
        
        # Draw L/R bars
        self._draw_bar(surface, x, y, self.rms_l, self.peak_hold_l, "L")
        self._draw_bar(surface, x + bar_width + 4, y, self.rms_r, self.peak_hold_r, "R")
    
    def _draw_bar(self, surface, x, y, rms_db, peak_db, label):
        """Draw a single level bar."""
        bar_width = self.width // 2 - 2
        
        # Background
        pygame.draw.rect(surface, self.color_bg, (x, y, bar_width, self.height))
        
        # Normalize levels to [0, 1]
        rms_norm = (rms_db - self.db_min) / (self.db_max - self.db_min)
        rms_norm = np.clip(rms_norm, 0.0, 1.0)
        
        peak_norm = (peak_db - self.db_min) / (self.db_max - self.db_min)
        peak_norm = np.clip(peak_norm, 0.0, 1.0)
        
        # Bar height from bottom
        bar_h = int(rms_norm * self.height)
        bar_y = y + self.height - bar_h
        
        # Color zones: green (-60 to -12), yellow (-12 to -6), red (-6 to 0)
        # Draw in segments
        for segment_y in range(bar_y, y + self.height, 2):
            segment_norm = 1.0 - (segment_y - y) / self.height
            segment_db = self.db_min + segment_norm * (self.db_max - self.db_min)
            
            if segment_db > -6:
                color = self.color_red
            elif segment_db > -12:
                color = self.color_yellow
            else:
                color = self.color_green
            
            pygame.draw.line(surface, color, (x + 1, segment_y), (x + bar_width - 1, segment_y))
        
        # Peak hold indicator
        peak_y = y + int((1.0 - peak_norm) * self.height)
        pygame.draw.line(surface, self.color_peak, (x, peak_y), (x + bar_width, peak_y), 2)
        
        # Border
        pygame.draw.rect(surface, self.color_border, (x, y, bar_width, self.height), 1)
        
        # Label at bottom
        label_text = self.font.render(label, True, (200, 200, 200))
        label_rect = label_text.get_rect(center=(x + bar_width // 2, y + self.height + 10))
        surface.blit(label_text, label_rect)
        
        # dB readout
        db_text = self.font.render(f"{int(rms_db)}dB", True, (150, 150, 150))
        db_rect = db_text.get_rect(center=(x + bar_width // 2, y + self.height + 22))
        surface.blit(db_text, db_rect)

