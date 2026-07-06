"""Preset catalog with research-aligned labels, EEG bands, and perception presets."""

# Binaural L/R center frequencies — kept low (≈150–250 Hz) for warmer, less fatiguing tones.
# L = carrier − beat/2,  R = carrier + beat/2  (beat frequency unchanged).
_C = {
    'delta': 150.0,
    'theta': 180.0,
    'alpha': 200.0,
    'beta': 220.0,
    'gamma': 250.0,
    'schumann': 174.0,  # low carrier; beat stays 7.83 Hz (geophysical fundamental)
}

PRESETS = [
    # --- Core brainwave (beat Hz aligned to standard EEG bands) ---
    {
        "id": "alpha_calm",
        "label": "Alpha — Calm (10 Hz)",
        "beat_hz": 10.0,
        "carrier_hz": _C['alpha'],
        "duration_min": 15,
        "mode": "binaural",
        "eeg_band": "alpha",
        "tags": ["evidence-informed"],
        "disclaimer": "Alpha band (8–12 Hz). Used in many relaxation/anxiety studies; effects vary. Not a medical device.",
        "description": "Mid-alpha — relaxed alertness, eyes-closed calm.",
        "category": "calm",
    },
    {
        "id": "theta_meditate",
        "label": "Theta — Meditate (6 Hz)",
        "beat_hz": 6.0,
        "carrier_hz": _C['theta'],
        "duration_min": 20,
        "mode": "binaural",
        "eeg_band": "theta",
        "tags": ["evidence-informed"],
        "disclaimer": "Theta band (4–8 Hz). Common in stress-reduction studies (~6 Hz); results vary. Not a medical device.",
        "description": "Mid-theta — meditation, hypnagogic imagery.",
        "category": "deep",
    },
    {
        "id": "delta_sleep",
        "label": "Delta — Deep Sleep (2 Hz)",
        "beat_hz": 2.0,
        "carrier_hz": _C['delta'],
        "duration_min": 30,
        "mode": "binaural",
        "eeg_band": "delta",
        "tags": ["experimental"],
        "disclaimer": "Delta band (0.5–4 Hz). Sleep studies exist (often 2–3 Hz) but evidence is small/mixed. Not a medical device.",
        "description": "Deep delta — aligns with slow-wave sleep band.",
        "category": "deep",
    },
    {
        "id": "beta_deepwork",
        "label": "Beta — Deep Work (18 Hz)",
        "beat_hz": 18.0,
        "carrier_hz": _C['beta'],
        "duration_min": 15,
        "mode": "binaural",
        "eeg_band": "beta",
        "tags": ["evidence-informed"],
        "disclaimer": "Beta band (13–30 Hz). Used in attention/cognition studies (~18 Hz); modest, mixed effects. Not a medical device.",
        "description": "Mid-beta — alert focus, active cognition.",
        "category": "focus",
    },
    {
        "id": "gamma_focus",
        "label": "Gamma — Peak Focus (40 Hz)",
        "beat_hz": 40.0,
        "carrier_hz": _C['gamma'],
        "duration_min": 10,
        "mode": "binaural",
        "eeg_band": "gamma",
        "tags": ["experimental"],
        "disclaimer": "Low gamma (≥30 Hz). Some cognition studies at 40 Hz; many use pulsed tones, not binaural beats. Mixed evidence.",
        "description": "40 Hz — low gamma; experimental cognitive binding.",
        "category": "focus",
    },
    {
        "id": "schumann",
        "label": "Schumann (7.83 Hz)",
        "beat_hz": 7.83,
        "carrier_hz": _C['schumann'],
        "duration_min": 20,
        "mode": "binaural",
        "eeg_band": "schumann",
        "tags": ["experimental"],
        "disclaimer": "Beat matches Earth–ionosphere fundamental (~7.83 Hz). Brain/wellness effects unproven. Not a medical device.",
        "description": "Geophysical resonance beat at a low, comfortable carrier.",
        "category": "explore",
    },

    # --- Hemi-Sync style (Monroe state names; not official Monroe frequencies) ---
    {
        "id": "hemisync_focus10",
        "label": "Focus 10 — Mind Awake",
        "beat_hz": 6.0,
        "carrier_hz": _C['theta'],
        "duration_min": 20,
        "mode": "binaural",
        "eeg_band": "theta",
        "tags": ["hemisync-style", "experimental"],
        "disclaimer": "Inspired by Monroe Focus 10 — not Hemi-Sync®. Uses theta (~6 Hz) for hypnagogic threshold; official tapes use proprietary multi-tone mixes.",
        "description": "Theta hypnagogic — mind awake, body near sleep.",
        "harmonic_layers": 2,
        "category": "deep",
    },
    {
        "id": "hemisync_focus12",
        "label": "Focus 12 — Expanded",
        "beat_hz": 7.0,
        "carrier_hz": _C['theta'],
        "duration_min": 25,
        "mode": "binaural",
        "eeg_band": "theta",
        "tags": ["hemisync-style", "experimental"],
        "disclaimer": "Inspired by Monroe Focus 12 — not Hemi-Sync®. Approximate high-theta; not an official reproduction.",
        "description": "High-theta — expanded awareness, hypnagogic depth.",
        "harmonic_layers": 2,
        "perception": "rotate",
        "category": "deep",
    },
    {
        "id": "hemisync_focus21",
        "label": "Focus 21 — Deep Theta",
        "beat_hz": 4.5,
        "carrier_hz": 165.0,
        "duration_min": 30,
        "mode": "binaural",
        "eeg_band": "theta",
        "tags": ["hemisync-style", "experimental"],
        "disclaimer": "Inspired by Monroe Focus 21 — not Hemi-Sync®. Deep theta (~4.5 Hz); marketing names like 'time/space' are not EEG terms.",
        "description": "Deep theta threshold — very low arousal.",
        "harmonic_layers": 2,
        "perception": "shimmer",
        "reverb": "cave",
        "category": "explore",
    },

    # --- Perception experiences (spatial/somatic; not band-specific claims) ---
    {
        "id": "rotate_theta",
        "label": "Rotating Theta (6 Hz)",
        "beat_hz": 6.0,
        "carrier_hz": 175.0,
        "duration_min": 20,
        "mode": "binaural",
        "eeg_band": "theta",
        "tags": ["perception", "experimental"],
        "disclaimer": "Theta band + spatial rotation effect. Experimental UX; not a medical device.",
        "description": "Mid-theta beat field slowly rotates around your head.",
        "perception": "rotate",
        "category": "explore",
    },
    {
        "id": "alternate_alpha",
        "label": "Alternate Alpha (10 Hz)",
        "beat_hz": 10.0,
        "carrier_hz": _C['alpha'],
        "duration_min": 15,
        "mode": "binaural",
        "eeg_band": "alpha",
        "tags": ["perception", "experimental"],
        "disclaimer": "Alpha band with alternating ear emphasis. Headphones still recommended for clearest binaural beat.",
        "description": "Mid-alpha with energy alternating between ears.",
        "perception": "alternate",
        "category": "explore",
    },
    {
        "id": "shimmer_meditation",
        "label": "Shimmer Alpha–Theta (8 Hz)",
        "beat_hz": 8.0,
        "carrier_hz": 190.0,
        "duration_min": 20,
        "mode": "binaural",
        "eeg_band": "alpha_theta",
        "tags": ["perception", "experimental"],
        "disclaimer": "8 Hz sits at alpha–theta border (alpha begins ~8 Hz). Experimental shimmer effect.",
        "description": "Alpha–theta border with ethereal amplitude shimmer.",
        "perception": "shimmer",
        "reverb": "chamber",
        "category": "calm",
    },
    {
        "id": "breath_alpha",
        "label": "Breath Sync Alpha (10 Hz)",
        "beat_hz": 10.0,
        "carrier_hz": _C['alpha'],
        "duration_min": 15,
        "mode": "binaural",
        "eeg_band": "alpha",
        "tags": ["perception", "experimental"],
        "disclaimer": "Mid-alpha with ~6/min volume swells (somatic pacing). Experimental; not clinical biofeedback.",
        "description": "Mid-alpha with breath-paced amplitude swells.",
        "perception": "breath",
        "category": "calm",
    },
    {
        "id": "float_cave",
        "label": "Float — Cave Reverb (5 Hz)",
        "beat_hz": 5.0,
        "carrier_hz": 170.0,
        "duration_min": 25,
        "mode": "binaural",
        "eeg_band": "theta",
        "tags": ["perception", "experimental"],
        "disclaimer": "Low-theta (5 Hz) with reverb spatialization. Experimental ambience.",
        "description": "Low-theta float in a spacious cave.",
        "perception": "breath",
        "reverb": "cave",
        "category": "deep",
    },
    {
        "id": "isochronic_alpha",
        "label": "Isochronic Alpha (10 Hz)",
        "beat_hz": 10.0,
        "carrier_hz": _C['alpha'],
        "duration_min": 15,
        "mode": "binaural",
        "eeg_band": "alpha",
        "tags": ["isochronic", "evidence-informed"],
        "disclaimer": "Mid-alpha isochronic pulses — works on speakers (no interaural separation needed). Effects still vary.",
        "description": "Speaker-friendly isochronic alpha pulses.",
        "isochronic": True,
        "category": "explore",
    },
]

PRESET_CATEGORIES = ['all', 'calm', 'deep', 'focus', 'explore']


def get_preset_by_id(preset_id):
    for p in PRESETS:
        if p["id"] == preset_id:
            return p
    return None


def get_all_presets():
    return PRESETS.copy()


def get_presets_by_category(category):
    if category == 'all':
        return PRESETS.copy()
    return [p for p in PRESETS if p.get('category', 'explore') == category]


def cycle_preset(current_id):
    if current_id is None:
        return PRESETS[0]
    for i, p in enumerate(PRESETS):
        if p["id"] == current_id:
            return PRESETS[(i + 1) % len(PRESETS)]
    return PRESETS[0]
