"""Clickable sidebar — presets, perception modes, reverb, controls."""

import pygame
from typing import Optional, Tuple, List

from toneflow.presets.catalog import PRESET_CATEGORIES, get_presets_by_category
from toneflow.audio.osc import PERCEPTION_LABELS


PANEL_WIDTH = 290

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
CAT_SEL = (70, 55, 110)


class ControlPanel:
    """Left sidebar with category filter, perception, reverb, and toggles."""

    def __init__(self, height: int, presets: list):
        self.height = height
        self.all_presets = presets
        self.filtered_presets: List[dict] = presets
        self.width = PANEL_WIDTH

        pygame.font.init()
        self.font_title = pygame.font.SysFont('Arial', 15, bold=True)
        self.font = pygame.font.SysFont('Arial', 13)
        self.font_small = pygame.font.SysFont('Arial', 11)

        self.selected_preset_idx = 0
        self.selected_preset_id = presets[0]['id'] if presets else ''
        self.preset_scroll = 0
        self.preset_row_h = 26
        self.max_visible_presets = 7
        self.hover_preset_idx: Optional[int] = None
        self.category = 'all'
        self.hover_category: Optional[str] = None

        self._mode = 'binaural'
        self._isochronic = False
        self._layers = 1
        self._reverb_preset = 'off'
        self._reverb_wet = 0.0
        self._perception = 'standard'
        self._noise_pink = False
        self._noise_white = False
        self._volume = 0.15
        self._session_active = False

        self._volume_track_rect = pygame.Rect(16, 0, PANEL_WIDTH - 32, 10)
        self._reverb_track_rect = pygame.Rect(16, 0, PANEL_WIDTH - 32, 10)
        self._dragging_volume = False
        self._dragging_reverb = False

        self._action_defs = [
            ('start_session', '▶  Start Session'),
            ('show_calibration', 'Calibrate SPL'),
            ('export', 'Export WAV'),
            ('show_about', 'About'),
            ('show_safety', 'Safety'),
        ]
        self._apply_category_filter()

    def _apply_category_filter(self):
        self.filtered_presets = get_presets_by_category(self.category)
        if not self.filtered_presets:
            self.filtered_presets = self.all_presets
        # Keep selection if possible
        for i, p in enumerate(self.filtered_presets):
            if p['id'] == self.selected_preset_id:
                self.selected_preset_idx = i
                self.preset_scroll = min(self.preset_scroll,
                                         max(0, len(self.filtered_presets) - self.max_visible_presets))
                return
        self.selected_preset_idx = 0
        self.preset_scroll = 0
        if self.filtered_presets:
            self.selected_preset_id = self.filtered_presets[0]['id']

    def sync_state(self, state: dict):
        self._mode = state.get('mode', 'binaural')
        self._isochronic = state.get('isochronic', False)
        self._layers = state.get('harmonic_layers', 1)
        self._reverb_preset = state.get('reverb_preset', 'off')
        self._reverb_wet = state.get('reverb_wet', 0.0)
        self._perception = state.get('perception', 'standard')
        self._noise_pink = state.get('noise_pink', False)
        self._noise_white = state.get('noise_white', False)
        self._volume = state.get('volume', 0.15)
        self._session_active = state.get('session_active', False)
        pid = state.get('preset_id', '')
        if pid:
            self.selected_preset_id = pid

    def _category_y(self) -> int:
        return 48

    def _preset_list_y(self) -> int:
        return self._category_y() + 28

    def _controls_y(self) -> int:
        return self._preset_list_y() + self.max_visible_presets * self.preset_row_h + 12

    def _volume_y(self) -> int:
        return self._controls_y() + 4 * 30 + 36

    def handle_event(self, event, window_width: int) -> Tuple[bool, dict]:
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if mx >= PANEL_WIDTH:
                return False, {}
            self._update_hover(mx, my)
            action = {}
            if self._dragging_volume:
                self._volume_from_mouse_x(mx)
                action['set_volume'] = self._volume
            if self._dragging_reverb:
                self._reverb_from_mouse_x(mx)
                action['set_reverb_wet'] = self._reverb_wet
            return True, action

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging_volume = False
            self._dragging_reverb = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if mx >= PANEL_WIDTH:
                return False, {}
            return True, self._click(mx, my)

        if event.type == pygame.MOUSEWHEEL:
            mx, _ = pygame.mouse.get_pos()
            if mx >= PANEL_WIDTH:
                return False, {}
            self.preset_scroll = max(0, self.preset_scroll - event.y)
            max_scroll = max(0, len(self.filtered_presets) - self.max_visible_presets)
            self.preset_scroll = min(self.preset_scroll, max_scroll)
            return True, {}

        return False, {}

    def _update_hover(self, mx, my):
        self.hover_preset_idx = None
        self.hover_category = None

        cy = self._category_y()
        x = 8
        for cat in PRESET_CATEGORIES:
            label = cat.capitalize()
            tw = self.font_small.size(label)[0] + 10
            rect = pygame.Rect(x, cy, tw, 20)
            if rect.collidepoint(mx, my):
                self.hover_category = cat
            x += tw + 4

        py = self._preset_list_y()
        for i in range(self.preset_scroll,
                       min(len(self.filtered_presets),
                           self.preset_scroll + self.max_visible_presets)):
            row = pygame.Rect(8, py + (i - self.preset_scroll) * self.preset_row_h,
                              PANEL_WIDTH - 16, self.preset_row_h - 2)
            if row.collidepoint(mx, my):
                self.hover_preset_idx = i

    def _click(self, mx, my) -> dict:
        # Category tabs
        cy = self._category_y()
        x = 8
        for cat in PRESET_CATEGORIES:
            label = cat.capitalize()
            tw = self.font_small.size(label)[0] + 10
            rect = pygame.Rect(x, cy, tw, 20)
            if rect.collidepoint(mx, my):
                self.category = cat
                self._apply_category_filter()
                idx = self.selected_preset_idx
                if self.filtered_presets:
                    return {'select_preset_id': self.filtered_presets[idx]['id']}
                return {}
            x += tw + 4

        # Preset list
        py = self._preset_list_y()
        for i in range(self.preset_scroll,
                       min(len(self.filtered_presets),
                           self.preset_scroll + self.max_visible_presets)):
            row = pygame.Rect(8, py + (i - self.preset_scroll) * self.preset_row_h,
                              PANEL_WIDTH - 16, self.preset_row_h - 2)
            if row.collidepoint(mx, my):
                return {'select_preset_id': self.filtered_presets[i]['id']}

        cy2 = self._controls_y()
        btn_w = (PANEL_WIDTH - 24) // 2 - 2
        btn_h = 26

        controls = [
            ('toggle_mode', None),
            ('toggle_isochronic', None),
            ('toggle_layers', None),
            ('cycle_perception', None),
            ('cycle_reverb', None),
            ('set_noise', 'pink'),
            ('set_noise', 'white'),
            (None, None),  # spacer
        ]
        for idx, (act_key, val) in enumerate(controls):
            if act_key is None:
                continue
            col = idx % 2
            row = idx // 2
            rect = pygame.Rect(8 + col * (btn_w + 4), cy2 + row * (btn_h + 4), btn_w, btn_h)
            if rect.collidepoint(mx, my):
                if val:
                    return {'set_noise': val}
                return {act_key: True}

        vol_y = self._volume_y()
        track = pygame.Rect(16, vol_y + 18, PANEL_WIDTH - 32, 10)
        self._volume_track_rect = track
        if track.inflate(0, 18).collidepoint(mx, my):
            self._dragging_volume = True
            self._volume_from_mouse_x(mx)
            return {'set_volume': self._volume}

        if self._reverb_preset != 'off':
            rev_y = vol_y + 44
            track = pygame.Rect(16, rev_y + 18, PANEL_WIDTH - 32, 10)
            self._reverb_track_rect = track
            if track.inflate(0, 18).collidepoint(mx, my):
                self._dragging_reverb = True
                self._reverb_from_mouse_x(mx)
                return {'set_reverb_wet': self._reverb_wet}

        act_y = vol_y + (88 if self._reverb_preset != 'off' else 44)
        for act_id, _ in self._action_defs:
            rect = pygame.Rect(8, act_y, PANEL_WIDTH - 16, 28)
            if rect.collidepoint(mx, my):
                return {act_id: True}
            act_y += 32

        return {}

    def _volume_from_mouse_x(self, mx):
        t = (mx - self._volume_track_rect.x) / max(1, self._volume_track_rect.width)
        self._volume = max(0.0, min(1.0, t))

    def _reverb_from_mouse_x(self, mx):
        t = (mx - self._reverb_track_rect.x) / max(1, self._reverb_track_rect.width)
        self._reverb_wet = max(0.05, min(0.40, t))

    def render(self, surface):
        pygame.draw.rect(surface, PANEL_BG, pygame.Rect(0, 0, PANEL_WIDTH, self.height))
        pygame.draw.line(surface, PANEL_BORDER,
                         (PANEL_WIDTH - 1, 0), (PANEL_WIDTH - 1, self.height), 2)

        surface.blit(self.font_title.render("ToneFlow", True, ACCENT), (12, 8))
        surface.blit(self.font_small.render("Perception Studio", True, TEXT_DIM), (12, 26))

        # Category tabs
        cy = self._category_y()
        x = 8
        for cat in PRESET_CATEGORIES:
            label = cat.capitalize()
            tw = self.font_small.size(label)[0] + 10
            rect = pygame.Rect(x, cy, tw, 20)
            if cat == self.category:
                pygame.draw.rect(surface, CAT_SEL, rect, border_radius=3)
            elif cat == self.hover_category:
                pygame.draw.rect(surface, BTN_HOVER, rect, border_radius=3)
            else:
                pygame.draw.rect(surface, BTN_BG, rect, border_radius=3)
            surface.blit(self.font_small.render(label, True, TEXT),
                         (rect.x + 5, rect.y + 3))
            x += tw + 4

        # Presets
        py = self._preset_list_y()
        for i in range(self.preset_scroll,
                       min(len(self.filtered_presets),
                           self.preset_scroll + self.max_visible_presets)):
            row = pygame.Rect(8, py + (i - self.preset_scroll) * self.preset_row_h,
                              PANEL_WIDTH - 16, self.preset_row_h - 2)
            pid = self.filtered_presets[i]['id']
            if pid == self.selected_preset_id:
                pygame.draw.rect(surface, PRESET_SEL, row, border_radius=3)
            elif i == self.hover_preset_idx:
                pygame.draw.rect(surface, BTN_HOVER, row, border_radius=3)
            else:
                pygame.draw.rect(surface, BTN_BG, row, border_radius=3)
            label = self.filtered_presets[i]['label']
            if len(label) > 30:
                label = label[:28] + '…'
            surface.blit(self.font_small.render(label, True, TEXT), (row.x + 6, row.y + 5))

        cy2 = self._controls_y()
        surface.blit(self.font_small.render("CONTROLS", True, TEXT_DIM), (12, cy2 - 12))

        btn_w = (PANEL_WIDTH - 24) // 2 - 2
        btn_h = 26
        labels = [
            ('Binaural' if self._mode == 'binaural' else 'Monaural', self._mode == 'binaural'),
            ('Isochronic', self._isochronic),
            (f'Layers {self._layers}', self._layers > 1),
            (PERCEPTION_LABELS.get(self._perception, 'Standard')[:14],
             self._perception != 'standard'),
            (f'Reverb {self._reverb_preset}', self._reverb_preset != 'off'),
            ('Pink', self._noise_pink),
            ('White', self._noise_white),
        ]
        for idx, (label, on) in enumerate(labels):
            col = idx % 2
            row = idx // 2
            rect = pygame.Rect(8 + col * (btn_w + 4), cy2 + row * (btn_h + 4), btn_w, btn_h)
            bg = BTN_ON if on else BTN_BG
            pygame.draw.rect(surface, bg, rect, border_radius=4)
            pygame.draw.rect(surface, PANEL_BORDER, rect, 1, border_radius=4)
            if len(label) > 13:
                label = label[:12] + '…'
            surface.blit(self.font_small.render(label, True, TEXT),
                         self.font_small.render(label, True, TEXT).get_rect(center=rect.center))

        vol_y = self._volume_y()
        surface.blit(self.font_small.render(f"Volume {int(self._volume * 100)}%", True, TEXT_DIM),
                     (12, vol_y))
        track = pygame.Rect(16, vol_y + 18, PANEL_WIDTH - 32, 10)
        pygame.draw.rect(surface, (30, 30, 40), track, border_radius=5)
        fw = int(track.width * self._volume)
        if fw > 0:
            pygame.draw.rect(surface, ACCENT, pygame.Rect(track.x, track.y, fw, track.height), border_radius=5)

        if self._reverb_preset != 'off':
            rev_y = vol_y + 44
            surface.blit(self.font_small.render(
                f"Reverb mix {int(self._reverb_wet * 100)}%", True, TEXT_DIM), (12, rev_y))
            rtrack = pygame.Rect(16, rev_y + 18, PANEL_WIDTH - 32, 10)
            self._reverb_track_rect = rtrack
            pygame.draw.rect(surface, (30, 30, 40), rtrack, border_radius=5)
            rw = int(rtrack.width * self._reverb_wet / 0.40)
            if rw > 0:
                pygame.draw.rect(surface, (120, 180, 220),
                                 pygame.Rect(rtrack.x, rtrack.y, rw, rtrack.height), border_radius=5)

        act_y = vol_y + (88 if self._reverb_preset != 'off' else 44)
        for act_id, label in self._action_defs:
            rect = pygame.Rect(8, act_y, PANEL_WIDTH - 16, 28)
            bg = BTN_ACTIVE if act_id == 'start_session' else BTN_BG
            if self._session_active and act_id == 'start_session':
                bg = BTN_ON
                label = '●  Session Active'
            pygame.draw.rect(surface, bg, rect, border_radius=4)
            surface.blit(self.font.render(label, True, TEXT),
                         self.font.render(label, True, TEXT).get_rect(center=rect.center))
            act_y += 32

        hy = self.height - 48
        surface.blit(self.font_small.render("Shift/Space + drag canvas → tune", True, ACCENT), (12, hy))

    def resize(self, height: int):
        self.height = height
