"""HUD overlay for canvas region: meters, gauge, tuning feedback."""

import pygame
from .meters import WaveformMeter, SpectrumMeter, LevelMeter


_BANDS = [
    (0.0,  4.0,  "δ Delta",  (30,   60, 200)),
    (4.0,  8.0,  "θ Theta",  (120,  40, 200)),
    (8.0,  12.0, "α Alpha",  (40,  200, 120)),
    (12.0, 30.0, "β Beta",   (220, 180,   0)),
    (30.0, 40.0, "γ Gamma",  (255, 255, 255)),
]
_BAND_MAX_HZ = 40.0


class HUD:
    """Heads-up display rendered over the canvas (right of control panel)."""

    def __init__(self, width, height, panel_width=270):
        self.width = width
        self.height = height
        self.panel_width = panel_width

        pygame.font.init()
        self.font_medium = pygame.font.SysFont('Arial', 15)
        self.font_small  = pygame.font.SysFont('Arial', 12)
        self.font_tiny   = pygame.font.SysFont('Arial', 11)

        self.text_color = (220, 220, 230)
        self.dim_color  = (120, 120, 130)
        self.safe_color = (80, 255, 120)
        self.accent     = (100, 180, 255)

        self.waveform_meter = WaveformMeter(width=260, height=60, duration_ms=100)
        self.spectrum_meter = SpectrumMeter(width=340, height=80, fft_size=1024)
        self.level_meter    = LevelMeter(width=48, height=110)

    def canvas_w(self):
        return self.width - self.panel_width

    def render(self, surface, state):
        ox = self.panel_width
        cw = self.canvas_w()

        # Tuning overlay when Shift/Space held
        if state.get('tuning_active'):
            self._render_tuning_overlay(surface, ox, cw, state)

        # Frequency readout (bottom of canvas)
        self._render_freq_readout(surface, ox, state)

        # Brainwave gauge (right edge of canvas)
        self._render_band_gauge(surface, ox, cw,
                                state.get('beat_hz', 10.0),
                                state.get('brainwave_state'))

        # SPL badge
        self._render_spl_badge(surface, ox, cw, state.get('spl_badge', 'green'))

        # Session timer
        if state.get('session_time') is not None:
            self._render_timer(surface, ox, cw,
                               state['session_time'], state.get('session_total'))

        # Audio meters
        if state.get('audio_chunk') is not None:
            self._render_meters(surface, ox, state['audio_chunk'], state.get('dt', 0.016))

    def _render_tuning_overlay(self, surface, ox, cw, state):
        canvas = pygame.Rect(ox, 0, cw, self.height)
        overlay = pygame.Surface((cw, self.height), pygame.SRCALPHA)
        overlay.fill((100, 180, 255, 18))
        surface.blit(overlay, (ox, 0))
        pygame.draw.rect(surface, self.accent, canvas, 2)

        # Axis labels
        surface.blit(self.font_small.render("Carrier 100 Hz", True, self.dim_color),
                     (ox + 12, self.height - 28))
        surface.blit(self.font_small.render("1000 Hz", True, self.dim_color),
                     (ox + cw - 58, self.height - 28))
        surface.blit(self.font_small.render("Beat 40 Hz", True, self.dim_color),
                     (ox + 12, 12))
        surface.blit(self.font_small.render("0 Hz", True, self.dim_color),
                     (ox + 12, self.height - 48))

        # Crosshair at current position
        cx, cy = state.get('tuning_cursor', (ox + cw // 2, self.height // 2))
        pygame.draw.line(surface, self.accent, (ox, cy), (ox + cw, cy), 1)
        pygame.draw.line(surface, self.accent, (cx, 0), (cx, self.height), 1)
        pygame.draw.circle(surface, self.accent, (cx, cy), 8, 2)

        hint = "Release Shift/Space to lock  |  Right-click: A/B compare"
        txt = self.font_tiny.render(hint, True, self.accent)
        surface.blit(txt, txt.get_rect(center=(ox + cw // 2, self.height - 14)))

    def _render_freq_readout(self, surface, ox, state):
        y = self.height - 100
        carrier = state.get('carrier_hz', 0)
        beat = state.get('beat_hz', 0)
        mode = state.get('mode', 'binaural')
        iso = state.get('isochronic', False)

        if iso:
            line = f"{carrier:.1f} Hz  ·  {beat:.2f} Hz beat  ·  Isochronic"
        elif mode == 'binaural':
            lf = carrier - beat / 2
            rf = carrier + beat / 2
            line = f"L {lf:.1f}  R {rf:.1f}  ·  Δ {beat:.2f} Hz"
        else:
            line = f"{carrier:.1f} Hz  ·  {beat:.2f} Hz  ·  {mode.title()}"

        bg = pygame.Surface((420, 22), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        surface.blit(bg, (ox + 12, y))
        surface.blit(self.font_medium.render(line, True, self.text_color), (ox + 16, y + 2))

    def _render_band_gauge(self, surface, ox, cw, beat_hz, brainwave_state):
        gauge_x = ox + cw - 90
        gauge_y = 70
        gauge_h = 240
        gauge_w = 12

        pygame.draw.rect(surface, (25, 25, 35),
                         (gauge_x - 2, gauge_y - 2, gauge_w + 4, gauge_h + 4))

        for low, high, name, colour in _BANDS:
            seg_top = gauge_y + int((1.0 - high / _BAND_MAX_HZ) * gauge_h)
            seg_bot = gauge_y + int((1.0 - low / _BAND_MAX_HZ) * gauge_h)
            seg_h = max(1, seg_bot - seg_top)
            dim_col = tuple(c // 4 for c in colour)
            pygame.draw.rect(surface, dim_col, (gauge_x, seg_top, gauge_w, seg_h))
            lbl = self.font_tiny.render(name, True, colour)
            surface.blit(lbl, (gauge_x + gauge_w + 4, seg_top + seg_h // 2 - 6))

        beat_clamped = max(0.0, min(beat_hz, _BAND_MAX_HZ))
        marker_y = gauge_y + int((1.0 - beat_clamped / _BAND_MAX_HZ) * gauge_h)
        band_col = brainwave_state[2] if brainwave_state else (255, 255, 255)
        pygame.draw.line(surface, band_col,
                         (gauge_x, marker_y), (gauge_x + gauge_w, marker_y), 2)

    def _render_spl_badge(self, surface, ox, cw, badge):
        colours = {'green': self.safe_color, 'amber': (255, 200, 0)}
        colour = colours.get(badge, (255, 80, 80))
        x = ox + cw - 50
        pygame.draw.circle(surface, colour, (x, 22), 10)
        surface.blit(self.font_tiny.render("SPL", True, colour),
                     self.font_tiny.render("SPL", True, colour).get_rect(center=(x, 22)))

    def _render_timer(self, surface, ox, cw, elapsed, total):
        m, s = int(elapsed // 60), int(elapsed % 60)
        txt = f"{m:02d}:{s:02d}"
        if total:
            tm, ts = int(total // 60), int(total % 60)
            txt += f" / {tm:02d}:{ts:02d}"
        t = self.font_medium.render(txt, True, self.text_color)
        surface.blit(t, t.get_rect(bottomright=(ox + cw - 100, self.height - 36)))

    def _render_meters(self, surface, ox, audio_chunk, dt):
        self.waveform_meter.update(audio_chunk)
        self.spectrum_meter.update(audio_chunk)
        self.level_meter.update(audio_chunk, dt)

        self.waveform_meter.render(surface, ox + 12, self.height - 175)
        self.spectrum_meter.render(surface, ox + (self.canvas_w() - 340) // 2, self.height - 95)
        self.level_meter.render(surface, ox + self.canvas_w() - 58, 380)

    def resize(self, width, height, panel_width=None):
        self.width = width
        self.height = height
        if panel_width is not None:
            self.panel_width = panel_width
