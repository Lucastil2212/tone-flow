"""About overlay with evidence-based copy and references."""

import pygame


class AboutOverlay:
    """
    Display evidence-based information about binaural/monaural beats.
    
    Content from spec section 6.
    """
    
    # Evidence-based copy per spec
    ABOUT_TEXT = """
ToneFlow — Binaural & Monaural Beat Generator

WHAT ARE BINAURAL BEATS?
A perceptual "third tone" created when two slightly different frequencies 
are presented separately to each ear. The beat frequency equals the difference 
between the two carrier tones.

EVIDENCE SUMMARY
Some studies and meta-analyses (2018/2019) report small–moderate benefits for 
anxiety and aspects of cognition with 10–30+ minute exposures. Results vary 
by protocol and listener.

Monaural beats (MB) can show stronger neural entrainment in some studies 
compared to binaural beats (BB), but mood effects are inconsistent.

PRESETS
• Alpha (10 Hz) / Theta (6 Hz) / Beta (18 Hz): Evidence-informed
• Gamma (40 Hz): Experimental focus (mixed evidence)
• Schumann (7.83 Hz): Reflects Earth-ionosphere resonance (physics); 
  wellness claims unproven
• Intuition Boost (528 Hz carrier): User preference, not evidence-based

REQUIREMENTS
• Headphones required for binaural beats (stereo separation needed)
• Adjust volume per calibration guidance

DISCLAIMER
ToneFlow is not a medical device. Effects vary by individual. 
Do not use as a substitute for professional medical advice.

Press A or Esc to close
""".strip()
    
    def __init__(self, width, height):
        """
        Initialize about overlay.
        
        Args:
            width: Window width
            height: Window height
        """
        self.width = width
        self.height = height
        
        pygame.font.init()
        self.font_title = pygame.font.SysFont('Arial', 20, bold=True)
        self.font_body = pygame.font.SysFont('Arial', 14)
        
        self.bg_color = (10, 10, 20, 230)  # Semi-transparent dark
        self.text_color = (220, 220, 230)
        self.title_color = (150, 200, 255)
    
    def render(self, surface):
        """
        Render about overlay.
        
        Args:
            surface: Pygame surface
        """
        # Semi-transparent background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill(self.bg_color)
        surface.blit(overlay, (0, 0))
        
        # Content box
        box_width = min(800, self.width - 80)
        box_height = min(600, self.height - 80)
        box_x = (self.width - box_width) // 2
        box_y = (self.height - box_height) // 2
        
        # Draw box
        pygame.draw.rect(surface, (20, 20, 40), 
                        (box_x, box_y, box_width, box_height))
        pygame.draw.rect(surface, (100, 100, 150), 
                        (box_x, box_y, box_width, box_height), 2)
        
        # Render text
        margin = 30
        y_pos = box_y + margin
        x_pos = box_x + margin
        max_width = box_width - 2 * margin
        
        lines = self.ABOUT_TEXT.split('\n')
        
        for line in lines:
            if y_pos + 20 > box_y + box_height - margin:
                break  # Don't overflow box
            
            # Title lines (all caps or section headers)
            if line.isupper() or line.startswith('•'):
                if line:
                    text = self.font_title.render(line, True, self.title_color)
                else:
                    y_pos += 10  # Blank line spacing
                    continue
            else:
                # Body text - wrap if needed
                if not line.strip():
                    y_pos += 10
                    continue
                
                # Simple word wrapping
                words = line.split()
                current_line = []
                
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    test_surface = self.font_body.render(test_line, True, self.text_color)
                    
                    if test_surface.get_width() > max_width and current_line:
                        # Render current line
                        text = self.font_body.render(' '.join(current_line), True, self.text_color)
                        surface.blit(text, (x_pos, y_pos))
                        y_pos += 20
                        current_line = [word]
                    else:
                        current_line.append(word)
                
                # Render remaining words
                if current_line:
                    text = self.font_body.render(' '.join(current_line), True, self.text_color)
                    surface.blit(text, (x_pos, y_pos))
                    y_pos += 20
                continue
            
            surface.blit(text, (x_pos, y_pos))
            y_pos += 25
    
    def resize(self, width, height):
        """Handle window resize."""
        self.width = width
        self.height = height


class SafetyOverlay:
    """
    Display safety information and SPL guidance.
    """
    
    SAFETY_TEXT = """
SAFE LISTENING GUIDANCE

NIOSH/OSHA STANDARDS
• 85 dBA over 8 hours is a key exposure benchmark
• ToneFlow warns near 80 dBA-equivalent (conservative estimate)

CALIBRATION
Press C to run calibration:
1. Pink noise will play (speech-like spectrum)
2. Adjust system volume so normal speech at arm's length is clear
3. This typically corresponds to ~60-70 dBA

SPL BADGE
• Green (<75 dBA): Safe for extended use
• Amber (75-80 dBA): Moderate; limit exposure time
• Red (>80 dBA): Reduce volume

RECOMMENDATIONS
• Use headphones for binaural beats (stereo separation required)
• Start with lower volumes and increase gradually
• Take breaks every 30-60 minutes
• Stop if you experience discomfort

Note: SPL estimation is approximate. For precise measurements, 
use a calibrated sound level meter.

Press S or Esc to close
""".strip()
    
    def __init__(self, width, height):
        """Initialize safety overlay."""
        self.width = width
        self.height = height
        
        pygame.font.init()
        self.font_title = pygame.font.SysFont('Arial', 20, bold=True)
        self.font_body = pygame.font.SysFont('Arial', 14)
        
        self.bg_color = (20, 10, 10, 230)
        self.text_color = (230, 220, 220)
        self.title_color = (255, 200, 150)
    
    def render(self, surface):
        """Render safety overlay."""
        # Similar to AboutOverlay but with safety text
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill(self.bg_color)
        surface.blit(overlay, (0, 0))
        
        box_width = min(700, self.width - 80)
        box_height = min(550, self.height - 80)
        box_x = (self.width - box_width) // 2
        box_y = (self.height - box_height) // 2
        
        pygame.draw.rect(surface, (40, 20, 20), 
                        (box_x, box_y, box_width, box_height))
        pygame.draw.rect(surface, (200, 100, 100), 
                        (box_x, box_y, box_width, box_height), 2)
        
        margin = 30
        y_pos = box_y + margin
        x_pos = box_x + margin
        max_width = box_width - 2 * margin
        
        lines = self.SAFETY_TEXT.split('\n')
        
        for line in lines:
            if y_pos + 20 > box_y + box_height - margin:
                break
            
            if line.isupper() or line.startswith('•'):
                if line:
                    text = self.font_title.render(line, True, self.title_color)
                else:
                    y_pos += 10
                    continue
            else:
                if not line.strip():
                    y_pos += 10
                    continue
                
                words = line.split()
                current_line = []
                
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    test_surface = self.font_body.render(test_line, True, self.text_color)
                    
                    if test_surface.get_width() > max_width and current_line:
                        text = self.font_body.render(' '.join(current_line), True, self.text_color)
                        surface.blit(text, (x_pos, y_pos))
                        y_pos += 20
                        current_line = [word]
                    else:
                        current_line.append(word)
                
                if current_line:
                    text = self.font_body.render(' '.join(current_line), True, self.text_color)
                    surface.blit(text, (x_pos, y_pos))
                    y_pos += 20
                continue
            
            surface.blit(text, (x_pos, y_pos))
            y_pos += 25
    
    def resize(self, width, height):
        """Handle window resize."""
        self.width = width
        self.height = height

