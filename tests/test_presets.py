"""Tests for preset definitions."""

import pytest
from toneflow.presets.catalog import (
    PRESETS,
    get_preset_by_id,
    get_all_presets,
    cycle_preset
)
from toneflow.presets.evidence import band_for_beat, beat_in_band, SCHUMANN_FUNDAMENTAL_HZ


def test_all_presets_valid():
    """Test that all presets have valid parameters."""
    assert len(PRESETS) >= 6  # Should have at least 6 presets
    
    for preset in PRESETS:
        # Check required fields
        assert 'id' in preset
        assert 'label' in preset
        assert 'beat_hz' in preset
        assert 'carrier_hz' in preset
        assert 'duration_min' in preset
        assert 'mode' in preset
        assert 'tags' in preset
        assert 'disclaimer' in preset
        
        # EEG band metadata
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
        
        # Check parameter ranges
        beat_hz = preset['beat_hz']
        assert 0.0 <= beat_hz <= 40.0, f"Beat Hz out of range: {beat_hz}"
        
        carrier_hz = preset['carrier_hz']
        assert 100.0 <= carrier_hz <= 1000.0, f"Carrier Hz out of range: {carrier_hz}"
        assert carrier_hz <= 280.0, f"Preset carrier should stay low for comfort: {carrier_hz}"
        
        # Check mode
        assert preset['mode'] in ['binaural', 'monaural']
        
        # Check tags
        assert isinstance(preset['tags'], list)
        valid_tags = ['evidence-informed', 'experimental', 'user-preference',
                      'hemisync-style', 'hemisync', 'journey', 'isochronic', 'perception']
        for tag in preset['tags']:
            assert tag in valid_tags


def test_preset_disclaimers():
    """Test that appropriate presets have disclaimers."""
    for preset in PRESETS:
        if 'experimental' in preset['tags']:
            # Experimental presets should have disclaimer
            assert 'disclaimer' in preset
            assert len(preset['disclaimer']) > 0
        
        if 'user-preference' in preset['tags']:
            # User preference presets should have disclaimer
            assert 'disclaimer' in preset
            assert 'not evidence-based' in preset['disclaimer'].lower()


def test_get_preset_by_id():
    """Test getting preset by ID."""
    preset = get_preset_by_id('alpha_calm')
    assert preset is not None
    assert preset['id'] == 'alpha_calm'
    assert preset['beat_hz'] == 10.0
    
    # Non-existent ID
    preset = get_preset_by_id('nonexistent')
    assert preset is None


def test_get_all_presets():
    """Test getting all presets returns a copy."""
    presets = get_all_presets()
    assert len(presets) == len(PRESETS)
    
    # Modify returned list shouldn't affect original
    presets.pop()
    assert len(get_all_presets()) == len(PRESETS)


def test_cycle_preset():
    """Test cycling through presets."""
    # Start from first
    preset = cycle_preset(None)
    assert preset['id'] == PRESETS[0]['id']
    
    # Cycle through all
    current_id = preset['id']
    for i in range(len(PRESETS)):
        next_preset = cycle_preset(current_id)
        assert next_preset is not None
        current_id = next_preset['id']
    
    # Should wrap around
    last_id = PRESETS[-1]['id']
    first_again = cycle_preset(last_id)
    assert first_again['id'] == PRESETS[0]['id']


def test_specific_presets():
    """Test specific preset configurations."""
    # Alpha/Calm
    alpha = get_preset_by_id('alpha_calm')
    assert alpha['beat_hz'] == 10.0
    assert 'evidence-informed' in alpha['tags']
    
    # Schumann
    schumann = get_preset_by_id('schumann')
    assert schumann['beat_hz'] == 7.83
    assert 'experimental' in schumann['tags']
    assert schumann['carrier_hz'] == 174.0
    
    # Delta — experimental, not evidence-informed
    delta = get_preset_by_id('delta_sleep')
    assert delta['beat_hz'] == 2.0
    assert 'experimental' in delta['tags']
    assert 'evidence-informed' not in delta['tags']
    
    # Hemi-Sync style — theta, not 528 Hz carrier
    focus10 = get_preset_by_id('hemisync_focus10')
    assert focus10['beat_hz'] == 6.0
    assert focus10['carrier_hz'] == 180.0
    assert 'hemisync-style' in focus10['tags']
    
    # Gamma/Focus
    gamma = get_preset_by_id('gamma_focus')
    assert gamma['beat_hz'] == 40.0
    assert 'experimental' in gamma['tags']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

