"""Shared modal dismiss helpers — Esc, click-outside, close button."""

import pygame
from typing import Optional, Tuple


CLOSE_HINT = "Esc  ·  click outside  ·  ✕ to close"


def close_button_rect(content_rect: pygame.Rect) -> pygame.Rect:
    return pygame.Rect(content_rect.right - 36, content_rect.top + 8, 28, 28)


def draw_close_button(surface, rect: pygame.Rect, hover: bool = False):
    bg = (180, 70, 70) if hover else (120, 50, 50)
    pygame.draw.rect(surface, bg, rect, border_radius=4)
    pygame.draw.rect(surface, (200, 200, 210), rect, 1, border_radius=4)
    cx, cy = rect.centerx, rect.centery
    pygame.draw.line(surface, (255, 255, 255), (cx - 6, cy - 6), (cx + 6, cy + 6), 2)
    pygame.draw.line(surface, (255, 255, 255), (cx + 6, cy - 6), (cx - 6, cy + 6), 2)


def draw_close_hint(surface, font, content_rect: pygame.Rect, y_offset: int = -28):
    hint = font.render(CLOSE_HINT, True, (140, 140, 155))
    surface.blit(hint, hint.get_rect(center=(content_rect.centerx, content_rect.bottom + y_offset)))


def check_modal_dismiss(event, content_rect: pygame.Rect,
                        close_rect: pygame.Rect,
                        close_keys: Tuple[int, ...] = ()) -> bool:
    """
    Return True if the user requested dismiss.

    close_keys: extra KEYDOWN keys that close (e.g. pygame.K_a for About).
    """
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            return True
        if event.key in close_keys:
            return True

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if close_rect.collidepoint(event.pos):
            return True
        if not content_rect.collidepoint(event.pos):
            return True

    return False
