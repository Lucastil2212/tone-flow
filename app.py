#!/usr/bin/env python3
"""
ToneFlow - Hemi-Sync style binaural/isochronic beat experience.
"""

import sys
import pygame
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from toneflow.audio.engine import AudioEngine
from toneflow.audio.export_wav import export_wav
from toneflow.presets.catalog import PRESETS, cycle_preset
from toneflow.ui.input import InputHandler
from toneflow.ui.hud import HUD
from toneflow.ui.control_panel import ControlPanel, PANEL_WIDTH
from toneflow.ui.about import AboutOverlay, SafetyOverlay
from toneflow.ui.calibrate import CalibrationHelper
from toneflow.ui.dialogs import MoodDialog, ExportDialog
from toneflow.viz.fallback2d import Fallback2DVisualizer
from toneflow.persist.history import SessionHistory


class ToneFlowApp:
    """Main ToneFlow application."""

    def __init__(self):
        self.width = 1280
        self.height = 720
        self.fps = 60

        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.init()

        self.screen = pygame.display.set_mode(
            (self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("ToneFlow — Hemi-Sync Binaural Experience")

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
        self.apply_preset(self.current_preset, 0)

        self.reverb_enabled = False
        self.noise_enabled = False
        self.noise_type = 'pink'
        self.show_about = False
        self.show_safety = False
        self.session_active = False
        self.session_start_mood = None

        self.was_tuning = False

        print("\nToneFlow ready.")
        print("  Use the left panel to pick presets and toggle controls.")
        print("  Hold Shift or Space + drag in the canvas to tune frequencies.")
        print("  Headphones recommended for binaural mode.\n")

    def apply_preset(self, preset, index):
        """Apply preset and reset audio mode flags from preset metadata."""
        self.current_preset = preset
        self.preset_index = index

        self.audio_engine.set_parameters(preset['carrier_hz'], preset['beat_hz'])
        self.audio_engine.set_mode(preset.get('mode', 'binaural'))
        self.audio_engine.isochronic_mode = preset.get('isochronic', False)
        self.audio_engine.harmonic_layers = preset.get('harmonic_layers', 1)
        self.audio_engine.harmonic_phases = [0.0, 0.0, 0.0]

        self.input_handler.carrier_hz = preset['carrier_hz']
        self.input_handler.beat_hz = preset['beat_hz']
        self.audio_engine.snap_parameters()

        print(f"Preset: {preset['label']}")

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
                    cal_result = self.calibration_helper.handle_event(event)
                    if cal_result == 'done':
                        print("Calibration complete")
                    elif cal_result == 'cancel':
                        print("Calibration cancelled")
                    handled = True

                if not handled:
                    consumed, panel_action = self.control_panel.handle_event(
                        event, self.width)
                    if panel_action:
                        self.handle_action(panel_action)

                    if not consumed:
                        action = self.input_handler.handle_event(event)
                        self.handle_action(action)

            self.audio_engine.update(dt)

            if self.was_tuning and not self.input_handler.is_tuning():
                self.audio_engine.snap_parameters()
            self.was_tuning = self.input_handler.is_tuning()

            if not self.session_active and self.input_handler.is_tuning():
                carrier, beat = self.input_handler.get_parameters()
                self.audio_engine.set_parameters(carrier, beat)

            self.visualizer.update(
                dt,
                self.audio_engine.beat_hz,
                self.audio_engine.carrier_hz,
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

        elif action.get('select_preset') is not None:
            idx = action['select_preset']
            if 0 <= idx < len(PRESETS):
                self.apply_preset(PRESETS[idx], idx)

        elif action.get('cycle_preset'):
            self.preset_index = (self.preset_index + 1) % len(PRESETS)
            self.apply_preset(PRESETS[self.preset_index], self.preset_index)

        elif action.get('start_session'):
            if not self.session_active:
                self.mood_dialog_pre = MoodDialog(self.width, self.height, mode='pre')
                self.mood_dialog_pre.show()

        elif action.get('ab_toggle'):
            self.input_handler.ab_toggle()
            c, b = self.input_handler.get_parameters()
            self.audio_engine.set_parameters(c, b)

        elif action.get('toggle_mode'):
            new_mode = 'monaural' if self.audio_engine.mode == 'binaural' else 'binaural'
            self.audio_engine.set_mode(new_mode)

        elif action.get('toggle_isochronic'):
            self.audio_engine.isochronic_mode = not self.audio_engine.isochronic_mode

        elif action.get('toggle_layers'):
            cur = self.audio_engine.harmonic_layers
            self.audio_engine.harmonic_layers = 1 if cur >= 3 else cur + 1

        elif action.get('toggle_reverb'):
            self.reverb_enabled = not self.reverb_enabled
            self.audio_engine.effects.set_reverb(self.reverb_enabled)

        elif action.get('set_noise'):
            noise_type = action['set_noise']
            if self.noise_enabled and self.noise_type == noise_type:
                self.noise_enabled = False
                self.audio_engine.effects.set_noise(False)
            else:
                self.noise_enabled = True
                self.noise_type = noise_type
                self.audio_engine.effects.set_noise(True, noise_type)

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
            self.hud.resize(w, h, PANEL_WIDTH)
            self.about_overlay.resize(w, h)
            self.safety_overlay.resize(w, h)
            self.calibration_helper.resize(w, h)
            self.control_panel.resize(h)
            self.visualizer.resize(w - PANEL_WIDTH, h)

    def start_session(self):
        duration_min = self.current_preset.get('duration_min', 15)
        self.audio_engine.start_session(duration_min)
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
                'reverb': {'enabled': self.reverb_enabled},
                'noise': {'enabled': self.noise_enabled,
                          'type': self.noise_type if self.noise_enabled else None},
            },
            duration_sec=elapsed,
            mood_pre=self.session_start_mood,
            mood_post=mood_post,
        )
        self.session_start_mood = None

    def do_export(self, duration_min):
        effects_config = {
            'reverb': {'enabled': self.reverb_enabled, 'wet_dry': 0.35},
            'noise': {'enabled': self.noise_enabled, 'type': self.noise_type, 'level_dbfs': -20.0},
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

        self.control_panel.sync_state({
            'mode': self.audio_engine.mode,
            'isochronic': self.audio_engine.isochronic_mode,
            'harmonic_layers': self.audio_engine.harmonic_layers,
            'reverb': self.reverb_enabled,
            'noise_pink': self.noise_enabled and self.noise_type == 'pink',
            'noise_white': self.noise_enabled and self.noise_type == 'white',
            'volume': self.audio_engine.master_volume,
            'session_active': self.session_active,
            'preset_index': self.preset_index,
        })
        self.control_panel.render(self.screen)

        tuning_cursor = None
        if self.input_handler.is_tuning():
            tuning_cursor = self.input_handler.get_tuning_cursor_pos()

        self.hud.render(self.screen, {
            'carrier_hz': self.audio_engine.carrier_hz,
            'beat_hz': self.audio_engine.beat_hz,
            'mode': self.audio_engine.mode,
            'isochronic': self.audio_engine.isochronic_mode,
            'brainwave_state': self.audio_engine.get_brainwave_state(),
            'session_time': elapsed if self.session_active else None,
            'session_total': total if self.session_active and total != float('inf') else None,
            'spl_badge': self.audio_engine.get_spl_badge(),
            'audio_chunk': self.audio_engine.get_last_chunk(),
            'dt': self.clock.get_time() / 1000.0,
            'tuning_active': self.input_handler.is_tuning(),
            'tuning_cursor': tuning_cursor,
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
        app = ToneFlowApp()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
