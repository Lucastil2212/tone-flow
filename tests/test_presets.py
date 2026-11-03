"""Tests for preset definitions."""

import pytest
from toneflow.presets.catalog import (
    PRESETS,
    PRESET_CATEGORIES,
    get_preset_by_id,
    get_all_presets,
    get_presets_by_category,
    cycle_preset,
)
from toneflow.presets.evidence import (
    band_for_beat,
    beat_in_band,
    SCHUMANN_FUNDAMENTAL_HZ,
    AESTHETIC_CARRIERS,
)


def test_all_presets_valid():
    """Test that all presets have valid parameters."""
    assert len(PRESETS) >= 6

    for preset in PRESETS:
        assert 'id' in preset
        assert 'label' in preset
        assert 'beat_hz' in preset
        assert 'carrier_hz' in preset
        assert 'duration_min' in preset
        assert 'mode' in preset
        assert 'tags' in preset
        assert 'disclaimer' in preset

        assert 'eeg_band' in preset
        band = preset['eeg_band']
        beat_hz = preset['beat_hz']
        if band == 'schumann':
            assert abs(beat_hz - SCHUMANN_FUNDAMENTAL_HZ) < 0.01
        elif band == 'alpha_theta':
            assert 7.5 <= beat_hz <= 8.5
        else:
            assert beat_in_band(beat_hz, band), (
                f"{preset['id']}: beat {beat_hz} Hz not in band {band}"
            )

        assert 0.0 <= beat_hz <= 40.0, f"Beat Hz out of range: {beat_hz}"

        carrier_hz = preset['carrier_hz']
        assert 100.0 <= carrier_hz <= 1000.0, f"Carrier Hz out of range: {carrier_hz}"

        # Comfort-band carriers for core presets; color/solfeggio may go higher
        is_color = (
            'color-vibration' in preset['tags']
            or 'user-preference' in preset['tags']
            or preset.get('category') == 'color'
        )
        if not is_color:
            assert carrier_hz <= 280.0, (
                f"Core preset carrier should stay low for comfort: {carrier_hz}"
            )

        assert preset['mode'] in ['binaural', 'monaural']

        assert isinstance(preset['tags'], list)
        valid_tags = [
            'evidence-informed', 'experimental', 'user-preference',
            'hemisync-style', 'hemisync', 'journey', 'isochronic',
            'perception', 'color-vibration',
        ]
        for tag in preset['tags']:
            assert tag in valid_tags

        if 'colour' in preset:
            c = preset['colour']
            assert len(c) == 3
            assert all(0 <= v <= 255 for v in c)


def test_preset_disclaimers():
    """Test that appropriate presets have disclaimers."""
    for preset in PRESETS:
        if 'experimental' in preset['tags']:
            assert 'disclaimer' in preset
            assert len(preset['disclaimer']) > 0

        if 'user-preference' in preset['tags']:
            assert 'disclaimer' in preset
            disc = preset['disclaimer'].lower()
            assert (
                'not evidence-based' in disc
                or 'not a medical' in disc
                or 'no established' in disc
                or 'traditional' in disc
            )


def test_color_vibration_presets():
    """Color category should expose solfeggio / chakra carriers with RGB."""
    color_presets = get_presets_by_category('color')
    assert len(color_presets) >= 7
    assert 'color' in PRESET_CATEGORIES

    for p in color_presets:
        assert 'colour' in p
        assert 'color-vibration' in p['tags'] or 'user-preference' in p['tags']
        assert p['carrier_hz'] in AESTHETIC_CARRIERS or p['id'] == 'schumann'


def test_get_preset_by_id():
    """Test getting preset by ID."""
    preset = get_preset_by_id('alpha_calm')
    assert preset is not None
    assert preset['id'] == 'alpha_calm'
    assert preset['beat_hz'] == 10.0

    solar = get_preset_by_id('color_solar_528')
    assert solar is not None
    assert solar['carrier_hz'] == 528.0
    assert solar['colour'] == (240, 210, 40)

    preset = get_preset_by_id('nonexistent')
    assert preset is None


def test_get_all_presets():
    """Test getting all presets returns a copy."""
    presets = get_all_presets()
    assert len(presets) == len(PRESETS)

    presets.pop()
    assert len(get_all_presets()) == len(PRESETS)


def test_cycle_preset():
    """Test cycling through presets."""
    preset = cycle_preset(None)
    assert preset['id'] == PRESETS[0]['id']

    current_id = preset['id']
    for i in range(len(PRESETS)):
        next_preset = cycle_preset(current_id)
        assert next_preset is not None
        current_id = next_preset['id']

    last_id = PRESETS[-1]['id']
    first_again = cycle_preset(last_id)
    assert first_again['id'] == PRESETS[0]['id']


def test_specific_presets():
    """Test specific preset configurations."""
    alpha = get_preset_by_id('alpha_calm')
    assert alpha['beat_hz'] == 10.0
    assert 'evidence-informed' in alpha['tags']

    schumann = get_preset_by_id('schumann')
    assert schumann['beat_hz'] == 7.83
    assert 'experimental' in schumann['tags']
    assert schumann['carrier_hz'] == 174.0

    delta = get_preset_by_id('delta_sleep')
    assert delta['beat_hz'] == 2.0
    assert 'experimental' in delta['tags']
    assert 'evidence-informed' not in delta['tags']

    focus10 = get_preset_by_id('hemisync_focus10')
    assert focus10['beat_hz'] == 6.0
    assert focus10['carrier_hz'] == 180.0
    assert 'hemisync-style' in focus10['tags']

    gamma = get_preset_by_id('gamma_focus')
    assert gamma['beat_hz'] == 40.0
    assert 'experimental' in gamma['tags']

    smr = get_preset_by_id('smr_focus')
    assert smr['beat_hz'] == 14.0
    assert beat_in_band(smr['beat_hz'], 'beta')


def test_band_for_beat():
    assert band_for_beat(10.0) == 'alpha'
    assert band_for_beat(7.83) == 'schumann'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
