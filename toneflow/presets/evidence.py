"""
Evidence notes and EEG band conventions for preset labeling.

EEG bands follow common clinical convention (e.g. Wikipedia/CDC summaries):
  Delta 0.5–4 Hz | Theta 4–8 Hz | Alpha 8–12 Hz | Beta 13–30 Hz | Gamma ≥30 Hz

Binaural-beat research (Garcia-Argibay 2018 meta-analysis; later reviews) reports
small–moderate effects on anxiety/cognition with protocol-dependent results.
Theta (~6 Hz) and alpha (~10 Hz) appear most often in relaxation studies;
beta (~18 Hz) in cognition studies; delta/gamma evidence is more mixed.
Schumann 7.83 Hz is a real geophysical resonance — wellness links are unproven.
Monroe Focus states are training labels, not published single-frequency protocols.
"""

from typing import Optional, Tuple

# (min_hz, max_hz) inclusive-ish upper bound for labeling
EEG_BANDS = {
    'delta': (0.5, 4.0),
    'theta': (4.0, 8.0),
    'alpha': (8.0, 12.0),
    'beta': (13.0, 30.0),
    'gamma': (30.0, 100.0),
    'schumann': (7.83, 7.83),  # geophysical, not an EEG band
    'alpha_theta': (8.0, 8.0),  # border label for 8 Hz presets
}

SCHUMANN_FUNDAMENTAL_HZ = 7.83

# Carriers sometimes marketed for wellness; no entrainment evidence for these values.
# Solfeggio / chakra tradition frequencies (aesthetic / exploratory only).
AESTHETIC_CARRIERS = {
    111.0, 136.1, 174.0, 285.0, 396.0, 417.0, 432.0,
    528.0, 639.0, 741.0, 852.0, 963.0,
}

# Traditional colour associations for solfeggio / chakra maps (not clinical).
COLOR_VIBRATION_MAP = {
    111.0: ('Bronze', (180, 140, 80)),
    136.1: ('Teal', (80, 160, 140)),
    174.0: ('Earth', (160, 60, 40)),
    285.0: ('Amber', (200, 100, 60)),
    396.0: ('Red', (220, 40, 40)),
    417.0: ('Orange', (255, 120, 30)),
    432.0: ('Sky', (100, 180, 220)),
    528.0: ('Yellow', (240, 210, 40)),
    639.0: ('Green', (40, 200, 100)),
    741.0: ('Blue', (40, 140, 255)),
    852.0: ('Indigo', (90, 60, 220)),
    963.0: ('Violet', (180, 120, 255)),
}


def band_for_beat(beat_hz: float) -> Optional[str]:
    """Return the best-matching EEG band name for a beat frequency."""
    if abs(beat_hz - SCHUMANN_FUNDAMENTAL_HZ) < 0.01:
        return 'schumann'
    for name in ('delta', 'theta', 'alpha', 'beta', 'gamma'):
        lo, hi = EEG_BANDS[name]
        if lo <= beat_hz <= hi:
            return name
    return None


def beat_in_band(beat_hz: float, band: str) -> bool:
    if band == 'schumann':
        return abs(beat_hz - SCHUMANN_FUNDAMENTAL_HZ) < 0.01
    if band not in EEG_BANDS:
        return False
    lo, hi = EEG_BANDS[band]
    return lo <= beat_hz <= hi
