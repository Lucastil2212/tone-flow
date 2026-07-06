"""Preset catalog with evidence-based labels and hemi-sync style experience presets."""

# ---------------------------------------------------------------------------
# Core brainwave presets (single frequency, evidence-informed)
# ---------------------------------------------------------------------------
PRESETS = [
    {
        "id": "alpha_calm",
        "label": "Alpha — Calm (10 Hz)",
        "beat_hz": 10.0,
        "carrier_hz": 512.0,
        "duration_min": 15,
        "mode": "binaural",
        "tags": ["evidence-informed"],
        "disclaimer": "Evidence-informed (relaxation). Effects vary. Not a medical device.",
        "description": "Alpha waves (8-12 Hz) — relaxed alertness, light meditation."
    },
    {
        "id": "theta_meditate",
        "label": "Theta — Meditate (6 Hz)",
        "beat_hz": 6.0,
        "carrier_hz": 440.0,
        "duration_min": 20,
        "mode": "binaural",
        "tags": ["evidence-informed"],
        "disclaimer": "Evidence-informed (deeper relaxation). Effects vary. Not a medical device.",
        "description": "Theta waves (4-8 Hz) — deep meditation, creativity, hypnagogic imagery."
    },
    {
        "id": "delta_sleep",
        "label": "Delta — Deep Sleep (2 Hz)",
        "beat_hz": 2.0,
        "carrier_hz": 256.0,
        "duration_min": 30,
        "mode": "binaural",
        "tags": ["evidence-informed"],
        "disclaimer": "Evidence-informed (sleep induction). Effects vary. Not a medical device.",
        "description": "Delta waves (0.5-4 Hz) — deep sleep, healing, unconscious processing."
    },
    {
        "id": "beta_deepwork",
        "label": "Beta — Deep Work (18 Hz)",
        "beat_hz": 18.0,
        "carrier_hz": 500.0,
        "duration_min": 15,
        "mode": "binaural",
        "tags": ["evidence-informed"],
        "disclaimer": "Evidence-informed (alertness). Effects vary. Not a medical device.",
        "description": "Beta waves (13-30 Hz) — focused attention, cognitive tasks."
    },
    {
        "id": "gamma_focus",
        "label": "Gamma — Peak Focus (40 Hz)",
        "beat_hz": 40.0,
        "carrier_hz": 600.0,
        "duration_min": 10,
        "mode": "binaural",
        "tags": ["experimental"],
        "disclaimer": "Experimental (mixed evidence). Not a medical device.",
        "description": "Gamma waves (≥30 Hz) — peak cognitive performance, binding."
    },
    {
        "id": "schumann",
        "label": "Schumann Resonance (7.83 Hz)",
        "beat_hz": 7.83,
        "carrier_hz": 432.0,
        "duration_min": 20,
        "mode": "binaural",
        "tags": ["experimental"],
        "disclaimer": "Experimental. Earth resonance (no proven wellness effect). Not a medical device.",
        "description": "The 7.83 Hz Schumann resonance — a real geophysical frequency."
    },

    # -----------------------------------------------------------------------
    # Hemi-Sync style experience presets
    # -----------------------------------------------------------------------
    {
        "id": "hemisync_focus10",
        "label": "Focus 10 — Mind Awake / Body Asleep",
        "beat_hz": 10.0,
        "carrier_hz": 528.0,
        "duration_min": 20,
        "mode": "binaural",
        "tags": ["hemisync", "evidence-informed"],
        "disclaimer": "Hemi-Sync style. Not a Monroe Institute product. Not a medical device.",
        "description": (
            "Inspired by Monroe Institute Focus 10 — carry waking consciousness "
            "while the body enters a relaxed, near-sleep state. Use with harmonic "
            "layers (L key) for the characteristic layered sound."
        ),
        "harmonic_layers": 2
    },
    {
        "id": "hemisync_focus12",
        "label": "Focus 12 — Expanded Awareness",
        "beat_hz": 7.0,
        "carrier_hz": 480.0,
        "duration_min": 25,
        "mode": "binaural",
        "tags": ["hemisync", "evidence-informed"],
        "disclaimer": "Hemi-Sync style. Not a Monroe Institute product. Not a medical device.",
        "description": (
            "Inspired by Focus 12 — state of expanded awareness beyond the "
            "physical. Theta-adjacent for vivid hypnagogic experience."
        ),
        "harmonic_layers": 2
    },
    {
        "id": "hemisync_focus21",
        "label": "Focus 21 — Edge of Time/Space",
        "beat_hz": 4.5,
        "carrier_hz": 396.0,
        "duration_min": 30,
        "mode": "binaural",
        "tags": ["hemisync", "experimental"],
        "disclaimer": "Hemi-Sync style / experimental. Not a medical device.",
        "description": (
            "Inspired by Focus 21 — the threshold between time/space and other "
            "energy systems. Deep theta for OBE-adjacent states."
        ),
        "harmonic_layers": 3
    },
    {
        "id": "journey_descent",
        "label": "Journey: Beta → Alpha → Theta",
        "beat_hz": 18.0,
        "carrier_hz": 500.0,
        "duration_min": 25,
        "mode": "binaural",
        "tags": ["journey", "evidence-informed"],
        "disclaimer": "Progressive entrainment. Effects vary. Not a medical device.",
        "description": (
            "Starts at Beta (alert), drifts through Alpha (calm), settles in "
            "Theta (deep). Mouse Y-axis overrides the descent — or just let it "
            "guide you down."
        ),
        "journey": [
            {"beat_hz": 18.0, "carrier_hz": 500.0, "duration_min": 3,  "label": "Beta Entry"},
            {"beat_hz": 10.0, "carrier_hz": 512.0, "duration_min": 7,  "label": "Alpha Calm"},
            {"beat_hz": 6.0,  "carrier_hz": 440.0, "duration_min": 12, "label": "Theta Depth"},
            {"beat_hz": 10.0, "carrier_hz": 512.0, "duration_min": 3,  "label": "Alpha Return"},
        ]
    },
    {
        "id": "isochronic_alpha",
        "label": "Isochronic Alpha (10 Hz pulse)",
        "beat_hz": 10.0,
        "carrier_hz": 440.0,
        "duration_min": 15,
        "mode": "binaural",   # engine will use isochronic when flag set
        "tags": ["isochronic", "evidence-informed"],
        "disclaimer": "Isochronic tones. Works without headphones. Not a medical device.",
        "description": (
            "Alpha entrainment via isochronic pulses — works through speakers. "
            "Press I to toggle isochronic mode on this or any preset."
        ),
        "isochronic": True
    },
]


def get_preset_by_id(preset_id):
    for p in PRESETS:
        if p["id"] == preset_id:
            return p
    return None


def get_all_presets():
    return PRESETS.copy()


def cycle_preset(current_id):
    if current_id is None:
        return PRESETS[0]
    for i, p in enumerate(PRESETS):
        if p["id"] == current_id:
            return PRESETS[(i + 1) % len(PRESETS)]
    return PRESETS[0]
