"""
Immersive 2D vibration visualizer.

Renders:
  - Deep-space background with twinkling star field
  - Soft radial bloom driven by RMS + colour vibration
  - Concentric ripple rings that expand at the beat frequency
  - Orbital particle field with trails (colour from band or preset)
  - Central breathing mandala with harmonic petal layers
  - Colour-vibration aura when a solfeggio/chakra preset is active
"""

import pygame
import numpy as np
import math
import colorsys


# ---------------------------------------------------------------------------
# Brainwave → colour palette
# ---------------------------------------------------------------------------
BAND_COLOURS = {
    "Delta":  ((10,  20, 120),  (30,  60, 200)),
    "Theta":  ((60,  10, 140),  (140, 40, 255)),
    "Alpha":  ((10,  80,  60),  (40, 200, 120)),
    "Beta":   ((120, 90,   0),  (240, 190, 10)),
    "Gamma":  ((120, 120, 120), (255, 255, 255)),
}

_DEFAULT_BAND = "Alpha"


def _lerp_colour(a, b, t):
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def _clamp_colour(c):
    return (max(0, min(255, int(c[0]))),
            max(0, min(255, int(c[1]))),
            max(0, min(255, int(c[2]))))


def _dim_of(rgb, factor=0.28):
    return _clamp_colour((rgb[0] * factor, rgb[1] * factor, rgb[2] * factor))


# ---------------------------------------------------------------------------
# Particle helper
# ---------------------------------------------------------------------------
class _OrbitalParticle:
    """A point orbiting the screen centre with a short trail."""

    __slots__ = ('cx', 'cy', 'angle', 'radius', 'speed', 'phase',
                 'size_base', 'z', 'trail', 'trail_len')

    def __init__(self, width, height, index, total):
        self.cx = width / 2
        self.cy = height / 2

        angle_spread = np.random.uniform(0, 2 * math.pi)
        self.angle = (2 * math.pi * index / total) + angle_spread
        self.radius = np.random.uniform(0.16, 0.48) * min(width, height)
        self.speed = np.random.uniform(0.08, 0.42)
        self.phase = np.random.uniform(0, 2 * math.pi)
        self.size_base = np.random.uniform(1.8, 5.5)
        self.z = np.random.uniform(0.55, 1.0)
        self.trail_len = 5
        self.trail = []

    def position(self):
        x = self.cx + self.radius * math.cos(self.angle)
        y = self.cy + self.radius * math.sin(self.angle)
        return x, y

    def update(self, dt, beat_hz, rms):
        beat_speed = 0.05 + 0.045 * beat_hz
        # Subtle radius breathing tied to beat
        self.angle += self.speed * beat_speed * dt
        self.angle %= 2 * math.pi
        # Radial vibration — tiny oscillation at beat rate
        vib = 1.0 + 0.012 * math.sin(self.phase + beat_hz * 2.0 * math.pi * 0)  # placeholder
        _ = vib  # radius modulated in render via phase
        px, py = self.position()
        self.trail.append((px, py))
        if len(self.trail) > self.trail_len:
            self.trail.pop(0)

    def resize(self, width, height):
        scale_x = width / max(self.cx * 2, 1)
        scale_y = height / max(self.cy * 2, 1)
        self.cx = width / 2
        self.cy = height / 2
        self.radius *= min(scale_x, scale_y)
        self.trail.clear()


# ---------------------------------------------------------------------------
# Ripple ring
# ---------------------------------------------------------------------------
class _RippleRing:
    """A circle that expands outward from the centre at each beat pulse."""

    __slots__ = ('radius', 'alpha', 'max_radius', 'active', 'thickness')

    def __init__(self):
        self.radius = 0.0
        self.alpha = 0.0
        self.max_radius = 0.0
        self.active = False
        self.thickness = 2

    def spawn(self, max_radius, thickness=2):
        self.radius = max_radius * 0.04
        self.alpha = 1.0
        self.max_radius = max_radius
        self.active = True
        self.thickness = thickness

    def update(self, dt, rms):
        if not self.active:
            return
        speed = 160.0 + 140.0 * rms
        self.radius += speed * dt
        self.alpha = max(0.0, 1.0 - (self.radius / self.max_radius))
        if self.alpha <= 0:
            self.active = False


# ---------------------------------------------------------------------------
# Main visualizer
# ---------------------------------------------------------------------------
class Fallback2DVisualizer:
    """
    Immersive 2D visualization for ToneFlow.

    Audio-reactive features:
    - Mandala breathes at beat_hz
    - Ring ripples spawn at each beat pulse
    - Orbital particles with trails accelerate with beat_hz
    - Colour from brainwave band OR preset colour vibration override
    - Glow / aura radius driven by RMS amplitude
    """

    N_RINGS = 8
    N_STARS = 160

    def __init__(self, width, height, n_particles=220, panel_offset=0):
        self.width = width
        self.height = height
        self.panel_offset = panel_offset
        self.n_particles = n_particles

        self.time = 0.0
        self.beat_hz = 10.0
        self.carrier_hz = 200.0
        self.rms = 0.0
        self.brainwave_state = ("Alpha", "relaxed alertness", (40, 200, 120))
        self.isochronic = False
        self.colour_override = None  # (r,g,b) from color presets

        self._bg_surface = None
        self._build_background()

        rng = np.random.default_rng(42)
        self._stars = [
            (float(rng.uniform(0, width)), float(rng.uniform(0, height)),
             int(rng.uniform(1, 3)), float(rng.uniform(0.25, 1.0)),
             float(rng.uniform(0.4, 2.5)))  # twinkle speed
            for _ in range(self.N_STARS)
        ]

        self._particles = [
            _OrbitalParticle(width, height, i, n_particles)
            for i in range(n_particles)
        ]

        self._rings = [_RippleRing() for _ in range(self.N_RINGS)]
        self._ring_idx = 0
        self._beat_phase = 0.0

        self._colour_dim = BAND_COLOURS[_DEFAULT_BAND][0]
        self._colour_bright = BAND_COLOURS[_DEFAULT_BAND][1]

        # Reusable alpha surfaces (avoid alloc every frame)
        self._glow_cache = {}
        self._aura_surf = pygame.Surface((width, height), pygame.SRCALPHA)

        pygame.font.init()
        self._font_state = pygame.font.SysFont('Arial', 26, bold=True)
        self._font_desc = pygame.font.SysFont('Arial', 14)
        self._font_hz = pygame.font.SysFont('Arial', 13)

    def _build_background(self):
        self._bg_surface = pygame.Surface((self.width, self.height))
        # Subtle vertical gradient — deeper at edges
        for y in range(self.height):
            t = y / max(self.height - 1, 1)
            # Slight radial feel via vertical darkening
            v = 6 + int(8 * (1.0 - abs(t - 0.5) * 1.4))
            self._bg_surface.fill((v, v, v + 6), rect=pygame.Rect(0, y, self.width, 1))

    def set_colour_override(self, rgb):
        """Set / clear preset colour vibration (RGB tuple or None)."""
        self.colour_override = rgb

    def update(self, dt, beat_hz, carrier_hz, rms,
               brainwave_state=None, isochronic=False, colour_override=None):
        self.time += dt
        self.beat_hz = max(0.1, beat_hz)
        self.carrier_hz = carrier_hz
        self.rms = min(1.0, rms * 8.0)
        self.isochronic = isochronic
        self.colour_override = colour_override

        if brainwave_state:
            self.brainwave_state = brainwave_state

        # Colour targets
        if self.colour_override is not None:
            target_bright = _clamp_colour(self.colour_override)
            target_dim = _dim_of(target_bright, 0.30)
        else:
            band_name = self.brainwave_state[0]
            target_dim, target_bright = BAND_COLOURS.get(
                band_name, BAND_COLOURS[_DEFAULT_BAND])

        smooth = min(1.0, dt * 2.0)
        self._colour_dim = _lerp_colour(self._colour_dim, target_dim, smooth)
        self._colour_bright = _lerp_colour(self._colour_bright, target_bright, smooth)

        # Beat-synced ring spawn
        prev_phase = self._beat_phase
        self._beat_phase = (self._beat_phase + dt * self.beat_hz) % 1.0
        if self._beat_phase < prev_phase:
            ring = self._rings[self._ring_idx % self.N_RINGS]
            max_r = min(self.width, self.height) * 0.55
            ring.spawn(max_r, thickness=2 if self.colour_override is None else 3)
            self._ring_idx += 1

        for ring in self._rings:
            ring.update(dt, self.rms)

        for p in self._particles:
            p.update(dt, self.beat_hz, self.rms)

    def render(self, surface, panel_offset=0):
        ox = panel_offset

        if ox > 0:
            surface.blit(self._bg_surface, (ox, 0))
        else:
            surface.blit(self._bg_surface, (0, 0))

        # Twinkling stars
        for sx, sy, ss, sb, tw in self._stars:
            twinkle = 0.55 + 0.45 * math.sin(self.time * tw + sx * 0.01)
            brightness = int(sb * twinkle * (110 + 80 * self.rms))
            brightness = max(20, min(255, brightness))
            col = (brightness, brightness, min(255, brightness + 28))
            pygame.draw.circle(surface, col, (ox + int(sx), int(sy)), ss)

        cx, cy = ox + self.width // 2, self.height // 2

        pulse = 0.5 + 0.5 * math.sin(2.0 * math.pi * self.beat_hz * self.time)
        breath = 0.84 + 0.16 * pulse

        dim = _clamp_colour(self._colour_dim)
        bright = _clamp_colour(self._colour_bright)
        mid = _clamp_colour(_lerp_colour(dim, bright, 0.5))

        # Colour-vibration aura (extra layer for solfeggio presets)
        if self.colour_override is not None:
            self._render_colour_aura(surface, cx, cy, pulse, bright)

        self._render_glow(surface, cx, cy, pulse, bright)

        for ring in self._rings:
            if ring.active and ring.alpha > 0.02:
                alpha = int(ring.alpha * (200 if self.colour_override else 170))
                r_col = _clamp_colour(_lerp_colour(dim, bright, ring.alpha))
                self._draw_circle_alpha(
                    surface, r_col, alpha, cx, cy,
                    int(ring.radius), max(1, int(ring.thickness * (0.5 + ring.alpha))))

        # Particles + trails
        for p in self._particles:
            # Radial micro-vibration
            vib = 1.0 + 0.018 * math.sin(
                self.time * self.beat_hz * 2.0 * math.pi + p.phase)
            px = p.cx + p.radius * vib * math.cos(p.angle)
            py = p.cy + p.radius * vib * math.sin(p.angle)

            col_t = 0.35 + 0.65 * p.z * (0.5 + 0.5 * math.sin(self.time * 1.3 + p.phase))
            col = _clamp_colour(_lerp_colour(dim, bright, col_t))
            sz = max(1, int(p.size_base * breath * p.z * (0.9 + 0.2 * self.rms)))

            # Trail
            for ti, (tx, ty) in enumerate(p.trail):
                fade = (ti + 1) / max(len(p.trail), 1)
                tcol = _clamp_colour((col[0] * fade * 0.45,
                                     col[1] * fade * 0.45,
                                     col[2] * fade * 0.45))
                pygame.draw.circle(surface, tcol,
                                   (ox + int(tx), int(ty)), max(1, sz - 1))

            pygame.draw.circle(surface, col, (ox + int(px), int(py)), sz)
            if sz >= 2:
                halo = _clamp_colour((col[0] // 3, col[1] // 3, col[2] // 3))
                pygame.draw.circle(surface, halo, (ox + int(px), int(py)), sz + 2)

        self._render_mandala(surface, cx, cy, breath, pulse, dim, mid, bright)
        self._render_state_label(surface, ox)

    def _render_colour_aura(self, surface, cx, cy, pulse, bright):
        """Soft expanding colour field for vibration presets."""
        base_r = int(min(self.width, self.height) * 0.42 * (0.92 + 0.08 * pulse))
        steps = 8
        for i in range(steps, 0, -1):
            t = i / steps
            r = int(base_r * t)
            # Hue-shift slightly over time for living vibration
            h, s, v = colorsys.rgb_to_hsv(bright[0] / 255, bright[1] / 255, bright[2] / 255)
            h = (h + 0.02 * math.sin(self.time * 0.35) * (1.0 - t)) % 1.0
            rr, gg, bb = colorsys.hsv_to_rgb(h, min(1.0, s * 0.9), v * 0.55)
            col = (int(rr * 255), int(gg * 255), int(bb * 255))
            alpha = int(22 * t * (0.5 + 0.5 * self.rms))
            self._draw_circle_alpha(surface, col, alpha, cx, cy, r, 0)

    def _render_glow(self, surface, cx, cy, pulse, bright):
        glow_r = int((min(self.width, self.height) * 0.30) * (0.88 + 0.22 * pulse))
        steps = 7
        for i in range(steps, 0, -1):
            t = i / steps
            r = int(glow_r * t)
            alpha = int(36 * t * (0.35 + 0.65 * self.rms))
            col = _clamp_colour(_lerp_colour((0, 0, 0), bright, t * 0.55))
            self._draw_circle_alpha(surface, col, alpha, cx, cy, r, 0)

    def _draw_circle_alpha(self, surface, colour, alpha, cx, cy, radius, width):
        if radius <= 0 or alpha <= 0:
            return
        diameter = radius * 2 + 4
        # Cache small glow discs; large rings still allocate (rare)
        key = (diameter, colour, alpha, width)
        tmp = self._glow_cache.get(key)
        if tmp is None:
            tmp = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            if width == 0:
                pygame.draw.circle(tmp, (*colour, alpha),
                                   (radius + 2, radius + 2), radius)
            else:
                pygame.draw.circle(tmp, (*colour, alpha),
                                   (radius + 2, radius + 2), radius, width)
            if len(self._glow_cache) < 64:
                self._glow_cache[key] = tmp
        surface.blit(tmp, (cx - radius - 2, cy - radius - 2))

    def _render_mandala(self, surface, cx, cy, breath, pulse, dim, mid, bright):
        t = self.time
        base_r = min(self.width, self.height) * 0.18 * breath

        petal_configs = [
            (8,  base_r * 0.98, base_r * 0.30, bright, 0),
            (12, base_r * 0.72, base_r * 0.18, mid,    math.pi / 12),
            (6,  base_r * 0.48, base_r * 0.22, dim,    math.pi / 6),
            (16, base_r * 1.12, base_r * 0.10, mid,    math.pi / 16),
        ]

        for n_petals, orbit_r, petal_half, colour, angle_offset in petal_configs:
            rotation = t * 0.14 * (1 if n_petals % 2 == 0 else -1)
            for k in range(n_petals):
                a = 2 * math.pi * k / n_petals + rotation + angle_offset
                px = cx + orbit_r * math.cos(a)
                py = cy + orbit_r * math.sin(a)
                pygame.draw.ellipse(
                    surface, colour,
                    (int(px - petal_half), int(py - petal_half * 0.55),
                     int(petal_half * 2), int(petal_half * 1.1)),
                    1
                )

        # Outer vibration dots
        n_dots = 32
        dot_orbit = base_r * 1.15
        dot_rot = t * 0.10
        for k in range(n_dots):
            a = 2 * math.pi * k / n_dots + dot_rot
            # Beat-synced size flicker
            flick = 0.7 + 0.3 * math.sin(a * 3 + pulse * math.pi)
            dx = int(cx + dot_orbit * math.cos(a))
            dy = int(cy + dot_orbit * math.sin(a))
            sz = max(1, int(2.8 * breath * flick))
            pygame.draw.circle(surface, bright, (dx, dy), sz)

        core_r = int(base_r * 0.24)
        pygame.draw.circle(surface, bright, (cx, cy), core_r)
        if core_r > 3:
            pygame.draw.circle(surface, (255, 255, 255),
                               (cx, cy), max(1, core_r // 3))

        # Secondary harmonic ring (carrier-linked)
        harm_r = int(base_r * (0.55 + 0.08 * math.sin(
            2 * math.pi * (self.carrier_hz / 200.0) * 0.15 * t)))
        self._draw_circle_alpha(surface, mid, 90, cx, cy, harm_r, 1)

        if self.isochronic:
            iso_r = int(base_r * 0.38 * (0.8 + 0.4 * pulse))
            iso_alpha = int(190 * pulse)
            self._draw_circle_alpha(surface, bright, iso_alpha, cx, cy, iso_r, 2)

    def _render_state_label(self, surface, ox=0):
        band_name, band_desc, _ = self.brainwave_state
        bright = _clamp_colour(self._colour_bright)

        mode_tag = " · ISOCHRONIC" if self.isochronic else ""
        color_tag = " · COLOR VIBRATION" if self.colour_override is not None else ""
        label_txt = self._font_state.render(
            f"{band_name.upper()} WAVE{mode_tag}{color_tag}", True, bright)
        desc_txt = self._font_desc.render(band_desc, True,
                                          _clamp_colour(self._colour_dim))
        hz_txt = self._font_hz.render(
            f"{self.carrier_hz:.0f} Hz carrier  ·  {self.beat_hz:.2f} Hz beat",
            True, _clamp_colour(_lerp_colour(self._colour_dim, bright, 0.4)))

        center_x = ox + self.width // 2
        surface.blit(label_txt, label_txt.get_rect(center=(center_x, 32)))
        surface.blit(desc_txt, desc_txt.get_rect(center=(center_x, 56)))
        surface.blit(hz_txt, hz_txt.get_rect(center=(center_x, 76)))

    def resize(self, width, height):
        old_w, old_h = self.width, self.height
        self.width = width
        self.height = height
        self._build_background()
        self._aura_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        self._glow_cache.clear()

        for p in self._particles:
            p.resize(width, height)

        sx = width / old_w if old_w else 1
        sy = height / old_h if old_h else 1
        self._stars = [
            (x * sx, y * sy, s, b, tw)
            for x, y, s, b, tw in self._stars
        ]
