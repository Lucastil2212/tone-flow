"""Calibration helper for SPL estimation."""

import pygame
from ..audio import osc


class CalibrationHelper:
    """
    Pink noise calibration flow.
    
    Plays pink noise and prompts user to adjust volume to comfortable speech level.
    """
    
    CALIBRATION_TEXT = """
SPL CALIBRATION

Pink noise is now playing.

INSTRUCTIONS:
1. Adjust your system volume so the noise level 
   matches normal speech at arm's length
2. This typically corresponds to ~60-70 dBA
3. Press SPACE when comfortable
4. Press ESC to cancel

The calibration will help estimate safe listening levels.
""".strip()
    
    def __init__(self, width, height, audio_engine):
        """
        Initialize calibration helper.
        
        Args:
            width: Window width
            height: Window height
            audio_engine: AudioEngine instance
        """
        self.width = width
        self.height = height
        self.audio_engine = audio_engine
        
        pygame.font.init()
        self.font_title = pygame.font.SysFont('Arial', 22, bold=True)
        self.font_body = pygame.font.SysFont('Arial', 16)
        
        self.bg_color = (15, 15, 25, 240)
        self.text_color = (220, 220, 230)
        self.title_color = (150, 255, 150)
        
        # Calibration state
        self.is_active = False
        self.calibration_channel = None
    
    def start_calibration(self):
        """Start calibration flow."""
        self.is_active = True
        
        # Generate pink noise for calibration (5 seconds, looped)
        pink_noise = osc.generate_pink_noise(5.0, 44100)
        
        # Normalize to reasonable level
        pink_noise *= 0.3
        
        # Convert to int16 for pygame
        pink_int16 = (pink_noise * 32767.0).astype('int16')
        sound = pygame.sndarray.make_sound(pink_int16)
        
        # Play looped
        self.calibration_channel = pygame.mixer.find_channel()
        if self.calibration_channel:
            self.calibration_channel.play(sound, loops=-1)
    
    def stop_calibration(self, save=False):
        """
        Stop calibration flow.
        
        Args:
            save: If True, save calibration offset
        """
        self.is_active = False
        
        if self.calibration_channel:
            self.calibration_channel.stop()
            self.calibration_channel = None
        
        if save:
            # Set calibration offset (assuming 65 dBA target for speech)
            self.audio_engine.set_spl_calibration(65.0)
    
    def handle_event(self, event):
        """
        Handle calibration events.
        
        Returns:
            'done' if calibration complete, 'cancel' if cancelled, None otherwise
        """
        if not self.is_active:
            return None
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.stop_calibration(save=True)
                return 'done'
            elif event.key == pygame.K_ESCAPE:
                self.stop_calibration(save=False)
                return 'cancel'
        
        return None
    
    def render(self, surface):
        """Render calibration overlay."""
        if not self.is_active:
            return
        
        # Semi-transparent background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill(self.bg_color)
        surface.blit(overlay, (0, 0))
        
        # Content box
        box_width = min(600, self.width - 80)
        box_height = min(400, self.height - 80)
        box_x = (self.width - box_width) // 2
        box_y = (self.height - box_height) // 2
        
        pygame.draw.rect(surface, (25, 35, 25), 
                        (box_x, box_y, box_width, box_height))
        pygame.draw.rect(surface, (100, 200, 100), 
                        (box_x, box_y, box_width, box_height), 3)
        
        # Render text
        margin = 30
        y_pos = box_y + margin
        x_pos = box_x + margin
        max_width = box_width - 2 * margin
        
        lines = self.CALIBRATION_TEXT.split('\n')
        
        for line in lines:
            if y_pos + 25 > box_y + box_height - margin:
                break
            
            if line.isupper():
                if line:
                    text = self.font_title.render(line, True, self.title_color)
                else:
                    y_pos += 15
                    continue
            else:
                if not line.strip():
                    y_pos += 10
                    continue
                
                # Word wrap
                words = line.split()
                current_line = []
                
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    test_surface = self.font_body.render(test_line, True, self.text_color)
                    
                    if test_surface.get_width() > max_width and current_line:
                        text = self.font_body.render(' '.join(current_line), True, self.text_color)
                        surface.blit(text, (x_pos, y_pos))
                        y_pos += 22
                        current_line = [word]
                    else:
                        current_line.append(word)
                
                if current_line:
                    text = self.font_body.render(' '.join(current_line), True, self.text_color)
                    surface.blit(text, (x_pos, y_pos))
                    y_pos += 22
                continue
            
            surface.blit(text, (x_pos, y_pos))
            y_pos += 28
        
        # Pulsing indicator
        pulse = 0.5 + 0.5 * ((pygame.time.get_ticks() / 500.0) % 1.0)
        indicator_color = (
            int(100 + 155 * pulse),
            int(200 + 55 * pulse),
            int(100 + 155 * pulse)
        )
        pygame.draw.circle(surface, indicator_color, 
                          (int(box_x + box_width // 2), int(box_y + box_height - 40)), 8)
    
    def resize(self, width, height):
        """Handle window resize."""
        self.width = width
        self.height = height

