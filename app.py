#!/usr/bin/env python3
"""ToneFlow — Hemi-Sync perception studio."""

import sys
import pygame
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from toneflow.audio.engine import AudioEngine
from toneflow.audio.export_wav import export_wav
from toneflow.presets.catalog import PRESETS, get_preset_by_id
from toneflow.ui.input import InputHandler
from toneflow.ui.hud import HUD
from toneflow.ui.control_panel import ControlPanel, PANEL_WIDTH
from toneflow.ui.about import AboutOverlay, SafetyOverlay
from toneflow.ui.calibrate import CalibrationHelper
from toneflow.ui.dialogs import MoodDialog, ExportDialog
from toneflow.viz.fallback2d import Fallback2DVisualizer
from toneflow.persist.history import SessionHistory


class ToneFlowApp:
    def __init__(self):
        self.width = 1280
        self.height = 720
        self.fps = 60

        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.init()

        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("ToneFlow — Perception Studio")

        canvas_w = self.width - PANEL_WIDTH
        self.visualizer = Fallback2DVisualizer(canvas_w, self.height, n_particles=200)
        self.audio_engine = AudioEngine(sample_rate=44100, buffer_size=2048)

        self.input_handler = InputHandler(self.width, self.height, PANEL_WIDTH)
        self.control_panel = ControlPanel(self.height, PRESETS)
        self.hud = HUD(self.width, self.height, PANEL_WIDTH)

        self.about_overlay = AboutOverlay(self.width, self.height)
        self.safety_overlay = SafetyOverlay(self.width, self.height)
        self.calibration_helper = CalibrationHelper(self.width, self.height, self.audio_engine)

        self.mood_dialog_pre = None
        self.mood_dialog_post = None
        self.export_dialog = None
        self.history = SessionHistory()

        self.running = True
        self.clock = pygame.time.Clock()

        self.current_preset = PRESETS[0]
        self.preset_index = 0
        self.apply_preset(self.current_preset)

        self.reverb_preset = 'off'
        self.noise_enabled = False
        self.noise_type = 'pink'
        self.show_about = False
        self.show_safety = False
        self.session_active = False
        self.session_start_mood = None
        self.was_tuning = False

        print("\nToneFlow — Perception Studio")
        print("  Panel: pick presets, perception mode, reverb space")
        print("  Shift/Space + drag canvas to tune frequencies\n")

    def apply_preset(self, preset):
        self.current_preset = preset
        for i, p in enumerate(PRESETS):
            if p['id'] == preset['id']:
                self.preset_index = i
                break

        self.audio_engine.set_parameters(preset['carrier_hz'], preset['beat_hz'])
        self.audio_engine.set_mode(preset.get('mode', 'binaural'))
        self.audio_engine.isochronic_mode = preset.get('isochronic', False)
        self.audio_engine.harmonic_layers = preset.get('harmonic_layers', 1)
        self.audio_engine.harmonic_phases = [0.0, 0.0, 0.0]
        self.audio_engine.set_perception_mode(preset.get('perception', 'standard'))
        self._perception_state_reset()

        rev = preset.get('reverb', 'off')
        self.reverb_preset = rev
        if rev != 'off':
            self.audio_engine.effects.set_reverb(True, preset=rev)
        else:
            self.audio_engine.effects.set_reverb(False)

        self.input_handler.carrier_hz = preset['carrier_hz']
        self.input_handler.beat_hz = preset['beat_hz']
        self.audio_engine.snap_parameters()
        print(f"Preset: {preset['label']}")

    def _perception_state_reset(self):
        self.audio_engine._perception_state = {
            'rotation_phase': 0.0, 'alt_phase': 0.0,
            'shimmer_phase': 0.0, 'breath_phase': 0.0,
        }

    def _modal_blocks_input(self):
        return (
            (self.mood_dialog_pre and self.mood_dialog_pre.is_active)
            or (self.mood_dialog_post and self.mood_dialog_post.is_active)
            or (self.export_dialog and self.export_dialog.is_active)
            or self.calibration_helper.is_active
            or self.show_about
            or self.show_safety
        )

    def run(self):
        while self.running:
            dt = self.clock.tick(self.fps) / 1000.0

            for event in pygame.event.get():
                handled = False

                if self.mood_dialog_pre and self.mood_dialog_pre.is_active:
                    result = self.mood_dialog_pre.handle_event(event)
                    if result is not None:
                        self.session_start_mood = result
                        self.start_session()
                    handled = True
                elif self.mood_dialog_post and self.mood_dialog_post.is_active:
                    result = self.mood_dialog_post.handle_event(event)
                    if result is not None:
                        self.end_session(result)
                    handled = True
                elif self.export_dialog and self.export_dialog.is_active:
                    result = self.export_dialog.handle_event(event)
                    if result is not None and result > 0:
                        self.do_export(result)
                    handled = True
                elif self.calibration_helper.is_active:
                    self.calibration_helper.handle_event(event)
                    handled = True
                elif self.show_about:
                    if self.about_overlay.handle_event(event):
                        self.show_about = False
                    handled = True
                elif self.show_safety:
                    if self.safety_overlay.handle_event(event):
                        self.show_safety = False
                    handled = True

                if not handled:
                    consumed, panel_action = self.control_panel.handle_event(event, self.width)
                    if panel_action:
                        self.handle_action(panel_action)
                    if not consumed:
                        skip_esc = (
                            event.type == pygame.KEYDOWN
                            and event.key == pygame.K_ESCAPE
                            and self._modal_blocks_input()
                        )
                        if not skip_esc:
                            self.handle_action(self.input_handler.handle_event(event))

            self.audio_engine.update(dt)

            if self.was_tuning and not self.input_handler.is_tuning():
                self.audio_engine.snap_parameters()
            self.was_tuning = self.input_handler.is_tuning()

            if not self.session_active and self.input_handler.is_tuning():
                c, b = self.input_handler.get_parameters()
                self.audio_engine.set_parameters(c, b)

            self.visualizer.update(
                dt, self.audio_engine.beat_hz, self.audio_engine.carrier_hz,
                self.audio_engine.current_rms,
                brainwave_state=self.audio_engine.get_brainwave_state(),
                isochronic=self.audio_engine.isochronic_mode,
            )
            self.render()
            pygame.display.flip()

        self.audio_engine.stop_session()
        pygame.quit()

    def handle_action(self, action):
        if not action:
            return

        if action.get('quit'):
            self.running = False

        elif action.get('select_preset_id'):
            preset = get_preset_by_id(action['select_preset_id'])
            if preset:
                self.apply_preset(preset)

        elif action.get('select_preset') is not None:
            idx = action['select_preset']
            if 0 <= idx < len(PRESETS):
                self.apply_preset(PRESETS[idx])

        elif action.get('start_session'):
            if not self.session_active:
                self.mood_dialog_pre = MoodDialog(self.width, self.height, mode='pre')
                self.mood_dialog_pre.show()

        elif action.get('toggle_mode'):
            m = 'monaural' if self.audio_engine.mode == 'binaural' else 'binaural'
            self.audio_engine.set_mode(m)

        elif action.get('toggle_isochronic'):
            self.audio_engine.isochronic_mode = not self.audio_engine.isochronic_mode

        elif action.get('toggle_layers'):
            cur = self.audio_engine.harmonic_layers
            self.audio_engine.harmonic_layers = 1 if cur >= 3 else cur + 1

        elif action.get('cycle_perception'):
            self.audio_engine.cycle_perception_mode()
            self._perception_state_reset()

        elif action.get('cycle_reverb'):
            self.reverb_preset = self.audio_engine.cycle_reverb()
            if self.reverb_preset != 'off' and self.audio_engine.effects.reverb:
                self.audio_engine.effects.reverb.set_wet(
                    self.audio_engine.effects.reverb.wet)

        elif action.get('set_reverb_wet') is not None:
            wet = action['set_reverb_wet']
            self.audio_engine.set_reverb_wet(wet)

        elif action.get('set_noise'):
            nt = action['set_noise']
            if self.noise_enabled and self.noise_type == nt:
                self.noise_enabled = False
                self.audio_engine.effects.set_noise(False)
            else:
                self.noise_enabled = True
                self.noise_type = nt
                self.audio_engine.effects.set_noise(True, nt)

        elif action.get('set_volume') is not None:
            self.audio_engine.set_volume(action['set_volume'])

        elif action.get('volume_up'):
            self.audio_engine.adjust_volume(0.05)
        elif action.get('volume_down'):
            self.audio_engine.adjust_volume(-0.05)

        elif action.get('export'):
            self.export_dialog = ExportDialog(self.width, self.height)
            self.export_dialog.show()
        elif action.get('show_about'):
            self.show_about = not self.show_about
        elif action.get('show_safety'):
            self.show_safety = not self.show_safety
        elif action.get('show_calibration'):
            if not self.calibration_helper.is_active:
                self.calibration_helper.start_calibration()

        elif action.get('resize'):
            w, h = action['resize']
            self.width, self.height = w, h
            self.input_handler.width = w
            self.input_handler.height = h
            self.input_handler.set_panel_width(PANEL_WIDTH)
            self.hud.resize(w, h, PANEL_WIDTH)
            self.about_overlay.resize(w, h)
            self.safety_overlay.resize(w, h)
            self.calibration_helper.resize(w, h)
            self.control_panel.resize(h)
            self.visualizer.resize(w - PANEL_WIDTH, h)

    def start_session(self):
        self.audio_engine.start_session(self.current_preset.get('duration_min', 15))
        self.session_active = True

    def end_session(self, mood_post):
        if not self.session_active:
            return
        self.session_active = False
        elapsed, _, _, _ = self.audio_engine.get_session_progress()
        self.history.add_session(
            preset_id=self.current_preset['id'],
            carrier_hz=self.audio_engine.carrier_hz,
            beat_hz=self.audio_engine.beat_hz,
            mode=self.audio_engine.mode,
            effects={
                'reverb': {'enabled': self.reverb_preset != 'off', 'preset': self.reverb_preset},
                'noise': {'enabled': self.noise_enabled,
                          'type': self.noise_type if self.noise_enabled else None},
            },
            duration_sec=elapsed,
            mood_pre=self.session_start_mood,
            mood_post=mood_post,
        )
        self.session_start_mood = None

    def do_export(self, duration_min):
        rev = self.reverb_preset
        wet = self.audio_engine.effects.reverb.wet if self.audio_engine.effects.reverb else 0.18
        effects_config = {
            'reverb': {'enabled': rev != 'off', 'preset': rev, 'wet_dry': wet},
            'noise': {'enabled': self.noise_enabled, 'type': self.noise_type, 'level_dbfs': -24.0},
        }
        filename = self.history.generate_export_filename(self.current_preset['id'])
        output_path = self.history.get_export_path(filename)
        try:
            export_wav(
                carrier_hz=self.audio_engine.carrier_hz,
                beat_hz=self.audio_engine.beat_hz,
                mode=self.audio_engine.mode,
                duration_min=duration_min,
                output_path=str(output_path),
                effects_config=effects_config,
            )
            print(f"Export complete: {output_path}")
        except Exception as e:
            print(f"Export failed: {e}")

    def render(self):
        self.screen.fill((6, 6, 14))
        self.visualizer.render(self.screen, panel_offset=PANEL_WIDTH)

        elapsed, total, _, _ = self.audio_engine.get_session_progress()
        rev_name, rev_wet = self.audio_engine.get_reverb_info()

        self.control_panel.sync_state({
            'mode': self.audio_engine.mode,
            'isochronic': self.audio_engine.isochronic_mode,
            'harmonic_layers': self.audio_engine.harmonic_layers,
            'reverb_preset': rev_name,
            'reverb_wet': rev_wet,
            'perception': self.audio_engine.perception_mode,
            'noise_pink': self.noise_enabled and self.noise_type == 'pink',
            'noise_white': self.noise_enabled and self.noise_type == 'white',
            'volume': self.audio_engine.master_volume,
            'session_active': self.session_active,
            'preset_id': self.current_preset['id'],
        })
        self.control_panel.render(self.screen)

        tc = self.input_handler.get_tuning_cursor_pos() if self.input_handler.is_tuning() else None
        self.hud.render(self.screen, {
            'carrier_hz': self.audio_engine.carrier_hz,
            'beat_hz': self.audio_engine.beat_hz,
            'mode': self.audio_engine.mode,
            'isochronic': self.audio_engine.isochronic_mode,
            'perception': self.audio_engine.perception_mode,
            'reverb_preset': rev_name,
            'brainwave_state': self.audio_engine.get_brainwave_state(),
            'session_time': elapsed if self.session_active else None,
            'session_total': total if self.session_active and total != float('inf') else None,
            'spl_badge': self.audio_engine.get_spl_badge(),
            'audio_chunk': self.audio_engine.get_last_chunk(),
            'dt': self.clock.get_time() / 1000.0,
            'tuning_active': self.input_handler.is_tuning(),
            'tuning_cursor': tc,
        })

        if self.show_about:
            self.about_overlay.render(self.screen)
        if self.show_safety:
            self.safety_overlay.render(self.screen)
        if self.calibration_helper.is_active:
            self.calibration_helper.render(self.screen)
        if self.mood_dialog_pre and self.mood_dialog_pre.is_active:
            self.mood_dialog_pre.render(self.screen)
        if self.mood_dialog_post and self.mood_dialog_post.is_active:
            self.mood_dialog_post.render(self.screen)
        if self.export_dialog and self.export_dialog.is_active:
            self.export_dialog.render(self.screen)

        if self.session_active and not self.audio_engine.is_playing:
            self.session_active = False
            self.mood_dialog_post = MoodDialog(self.width, self.height, mode='post')
            self.mood_dialog_post.show()


def main():
    try:
        ToneFlowApp().run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
