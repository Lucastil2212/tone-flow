"""Input handling: modifier-gated mouse tuning + keyboard shortcuts."""

import pygame


class InputHandler:
    """
    Mouse tuning only while Shift OR Space is held (in the canvas area).
    Normal mouse movement is free for clicking UI controls.

    Keyboard shortcuts remain available as secondary controls.
    """

    def __init__(self, width, height, panel_width=270):
        self.width = width
        self.height = height
        self.panel_width = panel_width

        self.carrier_hz = 512.0
        self.beat_hz = 10.0

        self.shift_held = False
        self.space_held = False

        self.tuning_active = False
        self.ab_slot = {'carrier_hz': 440.0, 'beat_hz': 8.0}
        self.quit_requested = False

    def set_panel_width(self, panel_width):
        self.panel_width = panel_width

    def is_tuning(self):
        return self.shift_held or self.space_held

    def canvas_rect(self):
        return pygame.Rect(self.panel_width, 0,
                           self.width - self.panel_width, self.height)

    def update_mouse_position(self, mouse_x, mouse_y):
        """Map canvas mouse position to carrier / beat when tuning."""
        canvas = self.canvas_rect()
        if not canvas.collidepoint(mouse_x, mouse_y):
            return

        local_x = mouse_x - canvas.x
        local_y = mouse_y - canvas.y

        t_x = local_x / max(1, canvas.width)
        t_y = 1.0 - (local_y / max(1, canvas.height))

        self.carrier_hz = 100.0 + t_x * 900.0
        self.beat_hz = t_y * 40.0

    def handle_event(self, event):
        action = {}

        if event.type == pygame.QUIT:
            action['quit'] = True
            self.quit_requested = True

        elif event.type == pygame.KEYDOWN:
            k = event.key
            if k == pygame.K_LSHIFT or k == pygame.K_RSHIFT:
                self.shift_held = True
            elif k == pygame.K_SPACE:
                self.space_held = True
            elif k == pygame.K_ESCAPE:
                action['quit'] = True
                self.quit_requested = True
            elif k == pygame.K_m:
                action['toggle_mode'] = True
            elif k == pygame.K_i:
                action['toggle_isochronic'] = True
            elif k == pygame.K_l:
                action['toggle_layers'] = True
            elif k == pygame.K_r:
                action['toggle_reverb'] = True
            elif k == pygame.K_n:
                action['set_noise'] = 'pink'
            elif k == pygame.K_w:
                action['set_noise'] = 'white'
            elif k == pygame.K_e:
                action['export'] = True
            elif k == pygame.K_a:
                action['show_about'] = True
            elif k == pygame.K_c:
                action['show_calibration'] = True
            elif k == pygame.K_s:
                action['show_safety'] = True
            elif k == pygame.K_UP:
                action['volume_up'] = True
            elif k == pygame.K_DOWN:
                action['volume_down'] = True
            elif k in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
                       pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9):
                action['select_preset'] = k - pygame.K_1

        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                self.shift_held = False
            elif event.key == pygame.K_SPACE:
                self.space_held = False

        elif event.type == pygame.MOUSEMOTION:
            if self.is_tuning():
                self.update_mouse_position(event.pos[0], event.pos[1])
                self.tuning_active = True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3 and self.is_tuning():
                action['ab_toggle'] = True

        elif event.type == pygame.VIDEORESIZE:
            self.width = event.w
            self.height = event.h
            action['resize'] = (event.w, event.h)

        return action

    def ab_toggle(self):
        self.carrier_hz, self.ab_slot['carrier_hz'] = (
            self.ab_slot['carrier_hz'], self.carrier_hz)
        self.beat_hz, self.ab_slot['beat_hz'] = (
            self.ab_slot['beat_hz'], self.beat_hz)

    def get_parameters(self):
        return self.carrier_hz, self.beat_hz

    def get_tuning_cursor_pos(self):
        """Return (x, y) of current carrier/beat mapped back to canvas coords."""
        canvas = self.canvas_rect()
        t_x = (self.carrier_hz - 100.0) / 900.0
        t_y = 1.0 - (self.beat_hz / 40.0)
        x = canvas.x + int(t_x * canvas.width)
        y = canvas.y + int((1.0 - t_y) * canvas.height)
        return x, y
