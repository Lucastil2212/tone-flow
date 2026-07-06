"""Clickable sidebar control panel for ToneFlow."""

import pygame
from typing import Optional, Tuple


PANEL_WIDTH = 270

PANEL_BG = (18, 18, 28)
PANEL_BORDER = (50, 50, 65)
BTN_BG = (35, 35, 50)
BTN_HOVER = (55, 55, 75)
BTN_ACTIVE = (60, 100, 140)
BTN_ON = (40, 120, 80)
TEXT = (220, 220, 230)
TEXT_DIM = (130, 130, 145)
ACCENT = (100, 180, 255)
PRESET_SEL = (45, 70, 110)


class ControlPanel:
    """Left sidebar: presets, toggles, volume slider, session controls."""

    def __init__(self, height: int, presets: list):
        self.height = height
        self.presets = presets
        self.width = PANEL_WIDTH

        pygame.font.init()
        self.font_title = pygame.font.SysFont('Arial', 15, bold=True)
        self.font = pygame.font.SysFont('Arial', 13)
        self.font_small = pygame.font.SysFont('Arial', 11)

        self.selected_preset_idx = 0
        self.preset_scroll = 0
        self.preset_row_h = 28
        self.max_visible_presets = 8
        self.hover_preset_idx: Optional[int] = None

        self._mode = 'binaural'
        self._isochronic = False
        self._layers = 1
        self._reverb = False
        self._noise_pink = False
        self._noise_white = False
        self._volume = 0.15
        self._session_active = False

        self._volume_track_rect = pygame.Rect(16, 0, PANEL_WIDTH - 32, 10)
        self._dragging_volume = False

        self._action_defs = [
            ('start_session', '▶  Start Session'),
            ('show_calibration', 'Calibrate SPL'),
            ('export', 'Export WAV'),
            ('show_about', 'About'),
            ('show_safety', 'Safety'),
        ]

    def sync_state(self, state: dict):
        self._mode = state.get('mode', 'binaural')
        self._isochronic = state.get('isochronic', False)
        self._layers = state.get('harmonic_layers', 1)
        self._reverb = state.get('reverb', False)
        self._noise_pink = state.get('noise_pink', False)
        self._noise_white = state.get('noise_white', False)
        self._volume = state.get('volume', 0.15)
        self._session_active = state.get('session_active', False)
        self.selected_preset_idx = state.get('preset_index', 0)

    def canvas_rect(self, window_width: int) -> pygame.Rect:
        return pygame.Rect(PANEL_WIDTH, 0, window_width - PANEL_WIDTH, self.height)

    def _toggle_y(self) -> int:
        return 52 + self.max_visible_presets * self.preset_row_h + 16

    def _volume_y(self) -> int:
        btn_h = 28
        return self._toggle_y() + 3 * (btn_h + 4) + 24

    def handle_event(self, event, window_width: int) -> Tuple[bool, dict]:
        """Returns (consumed, action_dict)."""
        action = {}

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if mx >= PANEL_WIDTH:
                return False, {}
            self._update_hover(mx, my)
            if self._dragging_volume:
                self._volume_from_mouse_x(mx)
                action['set_volume'] = self._volume
            return True, action

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging_volume = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if mx >= PANEL_WIDTH:
                return False, {}
            act = self._click(mx, my)
            return True, act

        if event.type == pygame.MOUSEWHEEL:
            mx, _ = pygame.mouse.get_pos()
            if mx >= PANEL_WIDTH:
                return False, {}
            self.preset_scroll = max(0, self.preset_scroll - event.y)
            max_scroll = max(0, len(self.presets) - self.max_visible_presets)
            self.preset_scroll = min(self.preset_scroll, max_scroll)
            return True, {}

        return False, {}

    def _update_hover(self, mx, my):
        self.hover_preset_idx = None
        preset_y = 52
        for i in range(self.preset_scroll,
                       min(len(self.presets), self.preset_scroll + self.max_visible_presets)):
            row = pygame.Rect(8, preset_y + (i - self.preset_scroll) * self.preset_row_h,
                              PANEL_WIDTH - 16, self.preset_row_h - 2)
            if row.collidepoint(mx, my):
                self.hover_preset_idx = i
                break

    def _click(self, mx, my) -> dict:
        preset_y = 52
        for i in range(self.preset_scroll,
                       min(len(self.presets), self.preset_scroll + self.max_visible_presets)):
            row = pygame.Rect(8, preset_y + (i - self.preset_scroll) * self.preset_row_h,
                              PANEL_WIDTH - 16, self.preset_row_h - 2)
            if row.collidepoint(mx, my):
                return {'select_preset': i}

        toggle_y = self._toggle_y()
        btn_w = (PANEL_WIDTH - 24) // 2 - 2
        btn_h = 28
        toggles = [
            ('toggle_mode', None),
            ('toggle_isochronic', None),
            ('toggle_layers', None),
            ('toggle_reverb', None),
            ('set_noise', 'pink'),
            ('set_noise', 'white'),
        ]
        for idx, (act_key, val) in enumerate(toggles):
            col = idx % 2
            row = idx // 2
            rect = pygame.Rect(8 + col * (btn_w + 4),
                               toggle_y + row * (btn_h + 4),
                               btn_w, btn_h)
            if rect.collidepoint(mx, my):
                if val:
                    return {'set_noise': val}
                return {act_key: True}

        vol_y = self._volume_y()
        track = pygame.Rect(16, vol_y + 18, PANEL_WIDTH - 32, 10)
        self._volume_track_rect = track
        if track.inflate(0, 20).collidepoint(mx, my):
            self._dragging_volume = True
            self._volume_from_mouse_x(mx)
            return {'set_volume': self._volume}

        act_y = vol_y + 44
        for act_id, _ in self._action_defs:
            rect = pygame.Rect(8, act_y, PANEL_WIDTH - 16, 30)
            if rect.collidepoint(mx, my):
                return {act_id: True}
            act_y += 34

        return {}

    def _volume_from_mouse_x(self, mx):
        track = self._volume_track_rect
        t = (mx - track.x) / max(1, track.width)
        self._volume = max(0.0, min(1.0, t))

    def render(self, surface):
        pygame.draw.rect(surface, PANEL_BG, pygame.Rect(0, 0, PANEL_WIDTH, self.height))
        pygame.draw.line(surface, PANEL_BORDER,
                         (PANEL_WIDTH - 1, 0), (PANEL_WIDTH - 1, self.height), 2)

        surface.blit(self.font_title.render("ToneFlow", True, ACCENT), (12, 10))
        surface.blit(self.font_small.render("Hemi-Sync Experience", True, TEXT_DIM), (12, 30))
        surface.blit(self.font_small.render("PRESETS  (scroll)", True, TEXT_DIM), (12, 48))

        preset_y = 52
        for i in range(self.preset_scroll,
                       min(len(self.presets), self.preset_scroll + self.max_visible_presets)):
            row = pygame.Rect(8, preset_y + (i - self.preset_scroll) * self.preset_row_h,
                              PANEL_WIDTH - 16, self.preset_row_h - 2)
            if i == self.selected_preset_idx:
                pygame.draw.rect(surface, PRESET_SEL, row, border_radius=3)
            elif i == self.hover_preset_idx:
                pygame.draw.rect(surface, BTN_HOVER, row, border_radius=3)
            else:
                pygame.draw.rect(surface, BTN_BG, row, border_radius=3)

            label = self.presets[i]['label']
            if len(label) > 28:
                label = label[:26] + '…'
            surface.blit(self.font_small.render(label, True, TEXT),
                         (row.x + 6, row.y + 6))

        toggle_y = self._toggle_y()
        surface.blit(self.font_small.render("CONTROLS", True, TEXT_DIM), (12, toggle_y - 14))

        btn_w = (PANEL_WIDTH - 24) // 2 - 2
        btn_h = 28
        toggle_labels = [
            ('Binaural' if self._mode == 'binaural' else 'Monaural', self._mode == 'binaural'),
            ('Isochronic', self._isochronic),
            (f'Layers {self._layers}', self._layers > 1),
            ('Reverb', self._reverb),
            ('Pink', self._noise_pink),
            ('White', self._noise_white),
        ]
        for idx, (label, on) in enumerate(toggle_labels):
            col = idx % 2
            row = idx // 2
            rect = pygame.Rect(8 + col * (btn_w + 4),
                               toggle_y + row * (btn_h + 4),
                               btn_w, btn_h)
            bg = BTN_ON if on else BTN_BG
            pygame.draw.rect(surface, bg, rect, border_radius=4)
            pygame.draw.rect(surface, PANEL_BORDER, rect, 1, border_radius=4)
            txt = self.font_small.render(label, True, TEXT)
            surface.blit(txt, txt.get_rect(center=rect.center))

        vol_y = self._volume_y()
        surface.blit(self.font_small.render(f"Volume  {int(self._volume * 100)}%", True, TEXT_DIM),
                     (12, vol_y))
        track = pygame.Rect(16, vol_y + 18, PANEL_WIDTH - 32, 10)
        self._volume_track_rect = track
        pygame.draw.rect(surface, (30, 30, 40), track, border_radius=5)
        fill_w = int(track.width * self._volume)
        if fill_w > 0:
            pygame.draw.rect(surface, ACCENT,
                             pygame.Rect(track.x, track.y, fill_w, track.height),
                             border_radius=5)
        knob_x = track.x + int(track.width * self._volume)
        pygame.draw.circle(surface, TEXT, (knob_x, track.centery), 6)

        act_y = vol_y + 44
        for act_id, label in self._action_defs:
            rect = pygame.Rect(8, act_y, PANEL_WIDTH - 16, 30)
            is_primary = act_id == 'start_session'
            bg = BTN_ACTIVE if is_primary else BTN_BG
            if self._session_active and act_id == 'start_session':
                bg = BTN_ON
                label = '●  Session Active'
            pygame.draw.rect(surface, bg, rect, border_radius=4)
            pygame.draw.rect(surface, PANEL_BORDER, rect, 1, border_radius=4)
            surface.blit(self.font.render(label, True, TEXT),
                         self.font.render(label, True, TEXT).get_rect(center=rect.center))
            act_y += 34

        hint_y = self.height - 52
        surface.blit(self.font_small.render("Tuning", True, TEXT_DIM), (12, hint_y))
        surface.blit(self.font_small.render("Hold Shift or Space", True, ACCENT), (12, hint_y + 14))
        surface.blit(self.font_small.render("+ drag in canvas", True, TEXT_DIM), (12, hint_y + 28))

    def resize(self, height: int):
        self.height = height
