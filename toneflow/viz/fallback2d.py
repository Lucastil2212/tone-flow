"""
Immersive 2D hemi-sync visualizer.

Renders:
  - Deep-space background with subtle star field
  - Central breathing mandala (geometric lotus petals)
  - Concentric ripple rings that expand at the beat frequency
  - Orbital particle field color-coded to brainwave state
  - Soft radial bloom / glow beneath the mandala
  - Screen-edge vignette for depth
"""

import pygame
import numpy as np
import math
import colorsys


# ---------------------------------------------------------------------------
# Brainwave → colour palette
# ---------------------------------------------------------------------------
BAND_COLOURS = {
    "Delta":  ((10,  20, 120),  (30,  60, 200)),   # (dim, bright)
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
    return (max(0, min(255, c[0])), max(0, min(255, c[1])), max(0, min(255, c[2])))


# ---------------------------------------------------------------------------
# Particle helper
# ---------------------------------------------------------------------------
class _OrbitalParticle:
    """A point orbiting the screen centre at a fixed radius and angular speed."""

    def __init__(self, width, height, index, total):
        self.cx = width / 2
        self.cy = height / 2

        angle_spread = np.random.uniform(0, 2 * math.pi)
        self.angle = (2 * math.pi * index / total) + angle_spread
        self.radius = np.random.uniform(0.18, 0.46) * min(width, height)
        self.speed = np.random.uniform(0.08, 0.35)   # rad/s base
        self.phase = np.random.uniform(0, 2 * math.pi)
        self.size_base = np.random.uniform(2.0, 5.0)
        self.z = np.random.uniform(0.6, 1.0)         # depth / brightness scale

    def position(self):
        x = self.cx + self.radius * math.cos(self.angle)
        y = self.cy + self.radius * math.sin(self.angle)
        return int(x), int(y)

    def update(self, dt, beat_hz, rms):
        # Orbital speed driven by beat frequency
        beat_speed = 0.05 + 0.04 * beat_hz
        self.angle += self.speed * beat_speed * dt
        self.angle %= 2 * math.pi

    def resize(self, width, height):
        scale_x = width / (self.cx * 2)
        scale_y = height / (self.cy * 2)
        self.cx = width / 2
        self.cy = height / 2
        self.radius *= min(scale_x, scale_y)


# ---------------------------------------------------------------------------
# Ripple ring
# ---------------------------------------------------------------------------
class _RippleRing:
    """A circle that expands outward from the centre at each beat pulse."""

    def __init__(self):
        self.radius = 0.0
        self.alpha = 0.0        # 0 = dead
        self.max_radius = 0.0
        self.active = False

    def spawn(self, max_radius, width, height):
        self.radius = max_radius * 0.05
        self.alpha = 1.0
        self.max_radius = max_radius
        self.active = True

    def update(self, dt, rms):
        if not self.active:
            return
        speed = 180.0 + 120.0 * rms
        self.radius += speed * dt
        self.alpha = max(0.0, 1.0 - (self.radius / self.max_radius))
        if self.alpha <= 0:
            self.active = False


# ---------------------------------------------------------------------------
# Main visualizer
# ---------------------------------------------------------------------------
class Fallback2DVisualizer:
    """
    Immersive 2D visualization for ToneFlow hemi-sync experience.

    Audio-reactive features:
    - Mandala breathes at beat_hz
    - Ring ripples spawn at each beat pulse
    - Orbital particles accelerate with beat_hz
    - Colour palette shifts with brainwave band (Delta/Theta/Alpha/Beta/Gamma)
    - Glow radius driven by RMS amplitude
    """

    N_RINGS = 6
    N_PETAL_SETS = 3
    N_STARS = 140

    def __init__(self, width, height, n_particles=180, panel_offset=0):
        self.width = width
        self.height = height
        self.panel_offset = panel_offset
        self.n_particles = n_particles

        self.time = 0.0
        self.beat_hz = 10.0
        self.carrier_hz = 512.0
        self.rms = 0.0
        self.brainwave_state = ("Alpha", "relaxed alertness", (40, 200, 120))
        self.isochronic = False

        # Pre-render background
        self._bg_surface = None
        self._build_background()

        # Stars (static)
        rng = np.random.default_rng(42)
        self._stars = [
            (int(rng.uniform(0, width)), int(rng.uniform(0, height)),
             int(rng.uniform(1, 3)), float(rng.uniform(0.3, 1.0)))
            for _ in range(self.N_STARS)
        ]

        # Orbital particles
        self._particles = [
            _OrbitalParticle(width, height, i, n_particles)
            for i in range(n_particles)
        ]

        # Ripple rings
        self._rings = [_RippleRing() for _ in range(self.N_RINGS)]
        self._ring_idx = 0
        self._beat_phase = 0.0       # tracks beat cycle for ring spawning
        self._last_beat_spawn = -999.0
        self._beat_period_est = 1.0  # seconds per beat

        # Smooth colour target
        self._colour_dim = BAND_COLOURS[_DEFAULT_BAND][0]
        self._colour_bright = BAND_COLOURS[_DEFAULT_BAND][1]
        self._colour_t = 0.0  # smooth interpolation progress

        # Off-screen glow surface
        self._glow_surf = pygame.Surface((width, height), pygame.SRCALPHA)

        # Font for state label
        pygame.font.init()
        self._font_state = pygame.font.SysFont('Arial', 28, bold=True)
        self._font_desc = pygame.font.SysFont('Arial', 15)

    # ------------------------------------------------------------------
    # Background (stars + vignette baked into a surface)
    # ------------------------------------------------------------------
    def _build_background(self):
        self._bg_surface = pygame.Surface((self.width, self.height))
        self._bg_surface.fill((6, 6, 14))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def update(self, dt, beat_hz, carrier_hz, rms,
               brainwave_state=None, isochronic=False):
        self.time += dt
        self.beat_hz = max(0.1, beat_hz)
        self.carrier_hz = carrier_hz
        self.rms = min(1.0, rms * 8.0)  # scale up the quiet signal
        self.isochronic = isochronic

        if brainwave_state:
            self.brainwave_state = brainwave_state

        # Update colour palette
        band_name = self.brainwave_state[0]
        target_dim, target_bright = BAND_COLOURS.get(band_name, BAND_COLOURS[_DEFAULT_BAND])
        smooth = min(1.0, dt * 1.5)
        self._colour_dim = _lerp_colour(self._colour_dim, target_dim, smooth)
        self._colour_bright = _lerp_colour(self._colour_bright, target_bright, smooth)

        # Update ring spawning (spawn on rising zero-crossing of beat sine)
        self._beat_period_est = 1.0 / self.beat_hz
        prev_phase = self._beat_phase
        self._beat_phase = (self._beat_phase + dt * self.beat_hz) % 1.0
        if self._beat_phase < prev_phase:  # wrapped → one beat elapsed
            ring = self._rings[self._ring_idx % self.N_RINGS]
            max_r = min(self.width, self.height) * 0.52
            ring.spawn(max_r, self.width, self.height)
            self._ring_idx += 1

        for ring in self._rings:
            ring.update(dt, self.rms)

        for p in self._particles:
            p.update(dt, self.beat_hz, self.rms)

    def render(self, surface, panel_offset=0):
        """Render into surface; panel_offset shifts drawing when using full window surface."""
        ox = panel_offset

        # 1. Background (canvas region only)
        bg = self._bg_surface
        if ox > 0:
            surface.blit(bg, (ox, 0))
        else:
            surface.blit(bg, (0, 0))

        # 2. Stars
        for sx, sy, ss, sb in self._stars:
            brightness = int(sb * (120 + 60 * self.rms))
            pygame.draw.circle(surface, (brightness, brightness, brightness + 20),
                               (ox + sx, sy), ss)

        cx, cy = ox + self.width // 2, self.height // 2

        pulse = 0.5 + 0.5 * math.sin(2.0 * math.pi * self.beat_hz * self.time)
        breath = 0.85 + 0.15 * pulse          # 0.85–1.0

        dim = _clamp_colour(self._colour_dim)
        bright = _clamp_colour(self._colour_bright)
        mid = _clamp_colour(_lerp_colour(dim, bright, 0.5))

        # 3. Glow bloom beneath mandala
        self._render_glow(surface, cx, cy, pulse, bright)

        # 4. Ripple rings
        for ring in self._rings:
            if ring.active and ring.alpha > 0.02:
                alpha = int(ring.alpha * 180)
                r_col = _clamp_colour(_lerp_colour(dim, bright, ring.alpha))
                self._draw_circle_alpha(surface, r_col, alpha, cx, cy,
                                        int(ring.radius), max(1, int(2 * ring.alpha)))

        # 5. Orbital particles
        for p in self._particles:
            pos = p.position()
            col_t = 0.4 + 0.6 * p.z * (0.5 + 0.5 * math.sin(self.time * 1.2 + p.phase))
            col = _clamp_colour(_lerp_colour(dim, bright, col_t))
            sz = max(1, int(p.size_base * breath * p.z))
            pygame.draw.circle(surface, col, (ox + pos[0], pos[1]), sz)
            # faint halo
            if sz >= 2:
                halo = _clamp_colour((col[0] // 3, col[1] // 3, col[2] // 3))
                pygame.draw.circle(surface, halo, (ox + pos[0], pos[1]), sz + 2)

        # 6. Central mandala
        self._render_mandala(surface, cx, cy, breath, pulse, dim, mid, bright)

        # 7. Brainwave state label (top-centre of canvas)
        self._render_state_label(surface, ox)

    # ------------------------------------------------------------------
    # Glow
    # ------------------------------------------------------------------
    def _render_glow(self, surface, cx, cy, pulse, bright):
        glow_r = int((min(self.width, self.height) * 0.28) * (0.9 + 0.2 * pulse))
        steps = 6
        for i in range(steps, 0, -1):
            t = i / steps
            r = int(glow_r * t)
            alpha = int(30 * t * (0.4 + 0.6 * self.rms))
            col = _clamp_colour(_lerp_colour((0, 0, 0), bright, t * 0.5))
            self._draw_circle_alpha(surface, col, alpha, cx, cy, r, 0)

    def _draw_circle_alpha(self, surface, colour, alpha, cx, cy, radius, width):
        """Draw a circle with transparency by blitting to a temp surface."""
        if radius <= 0:
            return
        diameter = radius * 2 + 4
        tmp = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        if width == 0:
            pygame.draw.circle(tmp, (*colour, alpha),
                               (radius + 2, radius + 2), radius)
        else:
            pygame.draw.circle(tmp, (*colour, alpha),
                               (radius + 2, radius + 2), radius, width)
        surface.blit(tmp, (cx - radius - 2, cy - radius - 2))

    # ------------------------------------------------------------------
    # Mandala
    # ------------------------------------------------------------------
    def _render_mandala(self, surface, cx, cy, breath, pulse, dim, mid, bright):
        """
        Draw a geometric mandala:
        - Outer ring of dots
        - 3 rings of petals (overlapping ellipses)
        - Central core circle with inner glow
        """
        t = self.time
        base_r = min(self.width, self.height) * 0.18 * breath

        # --- Petal layers ---
        petal_configs = [
            (8,  base_r * 0.95, base_r * 0.28, bright, 0),
            (12, base_r * 0.70, base_r * 0.18, mid,    math.pi / 12),
            (6,  base_r * 0.50, base_r * 0.22, dim,    math.pi / 6),
        ]

        for n_petals, orbit_r, petal_half, colour, angle_offset in petal_configs:
            rotation = t * 0.12 * (1 if n_petals % 2 == 0 else -1)
            for k in range(n_petals):
                a = 2 * math.pi * k / n_petals + rotation + angle_offset
                px = cx + orbit_r * math.cos(a)
                py = cy + orbit_r * math.sin(a)
                # Draw an ellipse oriented radially
                pygame.draw.ellipse(
                    surface, colour,
                    (int(px - petal_half), int(py - petal_half * 0.55),
                     int(petal_half * 2), int(petal_half * 1.1)),
                    1
                )

        # --- Outer dot ring ---
        n_dots = 24
        dot_orbit = base_r * 1.08
        dot_rot = t * 0.08
        for k in range(n_dots):
            a = 2 * math.pi * k / n_dots + dot_rot
            dx = int(cx + dot_orbit * math.cos(a))
            dy = int(cy + dot_orbit * math.sin(a))
            sz = max(1, int(2.5 * breath))
            pygame.draw.circle(surface, bright, (dx, dy), sz)

        # --- Inner core ---
        core_r = int(base_r * 0.22)
        pygame.draw.circle(surface, bright, (cx, cy), core_r)
        if core_r > 3:
            pygame.draw.circle(surface, (255, 255, 255),
                               (cx, cy), max(1, core_r // 3))

        # --- Isochronic indicator: pulsing ring around core ---
        if self.isochronic:
            iso_r = int(base_r * 0.35 * (0.8 + 0.4 * pulse))
            iso_alpha = int(180 * pulse)
            self._draw_circle_alpha(surface, bright, iso_alpha, cx, cy, iso_r, 2)

    # ------------------------------------------------------------------
    # State label
    # ------------------------------------------------------------------
    def _render_state_label(self, surface, ox=0):
        band_name, band_desc, _ = self.brainwave_state
        bright = _clamp_colour(self._colour_bright)

        mode_tag = " · ISOCHRONIC" if self.isochronic else ""
        label_txt = self._font_state.render(
            f"{band_name.upper()} WAVE{mode_tag}", True, bright)
        desc_txt = self._font_desc.render(band_desc, True,
                                          _clamp_colour(self._colour_dim))

        center_x = ox + self.width // 2
        label_rect = label_txt.get_rect(center=(center_x, 36))
        desc_rect = desc_txt.get_rect(center=(center_x, 62))
        surface.blit(label_txt, label_rect)
        surface.blit(desc_txt, desc_rect)

    # ------------------------------------------------------------------
    # Resize
    # ------------------------------------------------------------------
    def resize(self, width, height):
        self.width = width
        self.height = height
        self._build_background()
        self._glow_surf = pygame.Surface((width, height), pygame.SRCALPHA)

        cx, cy = width / 2, height / 2
        for p in self._particles:
            p.resize(width, height)

        # Rescale star positions
        old_w = self._bg_surface.get_width() if self._bg_surface else width
        old_h = self._bg_surface.get_height() if self._bg_surface else height
        sx = width / old_w if old_w else 1
        sy = height / old_h if old_h else 1
        self._stars = [
            (int(x * sx), int(y * sy), s, b)
            for x, y, s, b in self._stars
        ]
