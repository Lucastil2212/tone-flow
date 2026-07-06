"""Dialog windows using pure pygame for export and mood tracking."""

import pygame
from typing import Optional, Dict


class Button:
    """Simple pygame button."""
    
    def __init__(self, rect, text, color=(70, 130, 180), hover_color=(100, 160, 210)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pygame.font.SysFont('Arial', 16)
    
    def handle_event(self, event):
        """Check if button was clicked."""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False
    
    def draw(self, surface):
        """Draw the button."""
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2)
        
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class Slider:
    """Simple horizontal slider."""
    
    def __init__(self, rect, min_val=1, max_val=5, initial_val=3):
        self.rect = pygame.Rect(rect)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.dragging = False
        self.font = pygame.font.SysFont('Arial', 14)
    
    def handle_event(self, event):
        """Handle slider interaction."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self._update_value(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_value(event.pos[0])
    
    def _update_value(self, mouse_x):
        """Update value based on mouse position."""
        relative_x = mouse_x - self.rect.x
        t = relative_x / self.rect.width
        t = max(0.0, min(1.0, t))
        self.value = int(self.min_val + t * (self.max_val - self.min_val))
    
    def draw(self, surface):
        """Draw the slider."""
        # Track
        pygame.draw.rect(surface, (60, 60, 70), self.rect)
        pygame.draw.rect(surface, (140, 140, 150), self.rect, 1)
        
        # Handle
        t = (self.value - self.min_val) / (self.max_val - self.min_val)
        handle_x = self.rect.x + int(t * self.rect.width)
        handle_rect = pygame.Rect(handle_x - 8, self.rect.y - 4, 16, self.rect.height + 8)
        pygame.draw.rect(surface, (100, 160, 210), handle_rect)
        pygame.draw.rect(surface, (200, 200, 200), handle_rect, 2)
        
        # Value text
        value_text = self.font.render(str(self.value), True, (220, 220, 230))
        value_rect = value_text.get_rect(center=(self.rect.centerx, self.rect.bottom + 15))
        surface.blit(value_text, value_rect)


class MoodDialog:
    """
    Simple mood rating dialog (1-5 sliders for calm and focus).
    """
    
    def __init__(self, width, height, mode='pre'):
        """
        Initialize mood dialog.
        
        Args:
            width: Window width
            height: Window height
            mode: 'pre' or 'post' session
        """
        self.width = width
        self.height = height
        self.mode = mode
        
        self.is_active = False
        self.result = None
        
        # Dialog dimensions
        self.dialog_width = 400
        self.dialog_height = 280
        self.dialog_x = (width - self.dialog_width) // 2
        self.dialog_y = (height - self.dialog_height) // 2
        
        # Fonts
        pygame.font.init()
        self.title_font = pygame.font.SysFont('Arial', 20, bold=True)
        self.label_font = pygame.font.SysFont('Arial', 14)
        
        # UI elements
        self.calm_slider = None
        self.focus_slider = None
        self.submit_button = None
        self.skip_button = None
    
    def show(self):
        """Show the mood dialog."""
        self.is_active = True
        self.result = None
        
        # Create sliders
        self.calm_slider = Slider(
            (self.dialog_x + 20, self.dialog_y + 100, self.dialog_width - 40, 20),
            min_val=1, max_val=5, initial_val=3
        )
        
        self.focus_slider = Slider(
            (self.dialog_x + 20, self.dialog_y + 170, self.dialog_width - 40, 20),
            min_val=1, max_val=5, initial_val=3
        )
        
        # Create buttons
        self.submit_button = Button(
            (self.dialog_x + 20, self.dialog_y + 220, 150, 40),
            'Submit',
            color=(70, 150, 70),
            hover_color=(100, 180, 100)
        )
        
        self.skip_button = Button(
            (self.dialog_x + self.dialog_width - 170, self.dialog_y + 220, 150, 40),
            'Skip',
            color=(120, 120, 120),
            hover_color=(150, 150, 150)
        )
    
    def hide(self):
        """Hide and clean up the dialog."""
        self.is_active = False
        self.calm_slider = None
        self.focus_slider = None
        self.submit_button = None
        self.skip_button = None
    
    def handle_event(self, event):
        """
        Handle UI events.
        
        Returns:
            Dict with mood ratings if submitted, empty dict if skipped, None if still active
        """
        if not self.is_active:
            return None
        
        # Handle sliders
        self.calm_slider.handle_event(event)
        self.focus_slider.handle_event(event)
        
        # Handle buttons
        if self.submit_button.handle_event(event):
            calm = self.calm_slider.value
            focus = self.focus_slider.value
            self.result = {'calm': calm, 'focus': focus}
            self.hide()
            return self.result
        
        if self.skip_button.handle_event(event):
            self.result = {}  # Empty dict = skipped
            self.hide()
            return self.result
        
        return None
    
    def render(self, surface):
        """Render the mood dialog."""
        if not self.is_active:
            return
        
        # Semi-transparent background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Dialog box
        dialog_rect = pygame.Rect(self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height)
        pygame.draw.rect(surface, (30, 30, 50), dialog_rect)
        pygame.draw.rect(surface, (100, 100, 150), dialog_rect, 3)
        
        # Title
        title_text = "Pre-Session Mood" if self.mode == 'pre' else "Post-Session Mood"
        title_surf = self.title_font.render(title_text, True, (220, 220, 230))
        title_rect = title_surf.get_rect(center=(self.dialog_x + self.dialog_width // 2, self.dialog_y + 25))
        surface.blit(title_surf, title_rect)
        
        # Calm label
        calm_label = self.label_font.render("How calm do you feel? (1-5)", True, (200, 200, 210))
        surface.blit(calm_label, (self.dialog_x + 20, self.dialog_y + 70))
        
        # Calm slider
        self.calm_slider.draw(surface)
        
        # Focus label
        focus_label = self.label_font.render("How focused do you feel? (1-5)", True, (200, 200, 210))
        surface.blit(focus_label, (self.dialog_x + 20, self.dialog_y + 140))
        
        # Focus slider
        self.focus_slider.draw(surface)
        
        # Buttons
        self.submit_button.draw(surface)
        self.skip_button.draw(surface)


class ExportDialog:
    """
    Export duration chooser dialog.
    """
    
    def __init__(self, width, height):
        """Initialize export dialog."""
        self.width = width
        self.height = height
        
        self.is_active = False
        self.result = None
        
        # Dialog dimensions
        self.dialog_width = 350
        self.dialog_height = 250
        self.dialog_x = (width - self.dialog_width) // 2
        self.dialog_y = (height - self.dialog_height) // 2
        
        # Fonts
        pygame.font.init()
        self.title_font = pygame.font.SysFont('Arial', 20, bold=True)
        self.option_font = pygame.font.SysFont('Arial', 16)
        
        # Duration options
        self.durations = [5, 10, 15, 20, 30]
        self.selected_index = 1  # Default to 10 min
        
        # UI elements
        self.duration_buttons = []
        self.export_button = None
        self.cancel_button = None
    
    def show(self):
        """Show the export dialog."""
        self.is_active = True
        self.result = None
        
        # Create duration option buttons
        self.duration_buttons = []
        button_y = self.dialog_y + 60
        for i, duration in enumerate(self.durations):
            button = Button(
                (self.dialog_x + 20, button_y + i * 28, 310, 25),
                f"{duration} minutes",
                color=(60, 60, 80) if i != self.selected_index else (70, 130, 180),
                hover_color=(80, 80, 100) if i != self.selected_index else (100, 160, 210)
            )
            self.duration_buttons.append(button)
        
        # Create action buttons
        self.export_button = Button(
            (self.dialog_x + 20, self.dialog_y + 200, 140, 35),
            'Export',
            color=(70, 150, 70),
            hover_color=(100, 180, 100)
        )
        
        self.cancel_button = Button(
            (self.dialog_x + self.dialog_width - 160, self.dialog_y + 200, 140, 35),
            'Cancel',
            color=(120, 120, 120),
            hover_color=(150, 150, 150)
        )
    
    def hide(self):
        """Hide and clean up the dialog."""
        self.is_active = False
        self.duration_buttons = []
        self.export_button = None
        self.cancel_button = None
    
    def handle_event(self, event):
        """
        Handle UI events.
        
        Returns:
            Duration in minutes if exported, 0 if cancelled, None if still active
        """
        if not self.is_active:
            return None
        
        # Handle duration selection
        for i, button in enumerate(self.duration_buttons):
            if button.handle_event(event):
                self.selected_index = i
                # Update button colors
                for j, btn in enumerate(self.duration_buttons):
                    if j == i:
                        btn.color = (70, 130, 180)
                        btn.hover_color = (100, 160, 210)
                    else:
                        btn.color = (60, 60, 80)
                        btn.hover_color = (80, 80, 100)
        
        # Handle action buttons
        if self.export_button.handle_event(event):
            self.result = self.durations[self.selected_index]
            self.hide()
            return self.result
        
        if self.cancel_button.handle_event(event):
            self.result = 0
            self.hide()
            return self.result
        
        return None
    
    def render(self, surface):
        """Render the export dialog."""
        if not self.is_active:
            return
        
        # Semi-transparent background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Dialog box
        dialog_rect = pygame.Rect(self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height)
        pygame.draw.rect(surface, (30, 30, 50), dialog_rect)
        pygame.draw.rect(surface, (100, 100, 150), dialog_rect, 3)
        
        # Title
        title_surf = self.title_font.render("Export Session to WAV", True, (220, 220, 230))
        title_rect = title_surf.get_rect(center=(self.dialog_x + self.dialog_width // 2, self.dialog_y + 25))
        surface.blit(title_surf, title_rect)
        
        # Duration buttons
        for button in self.duration_buttons:
            button.draw(surface)
        
        # Action buttons
        self.export_button.draw(surface)
        self.cancel_button.draw(surface)
