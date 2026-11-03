"""OpenGL particle field visualization with beat-pulse and carrier-hue mapping."""

import numpy as np
import colorsys
import time

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False


class ParticleField:
    """
    3D particle field visualizer using OpenGL.
    
    Features:
    - Particle scale pulses with beat frequency
    - Hue mapped from carrier (20 Hz → blue, 1000 Hz → red)
    - Brightness driven by RMS amplitude
    - Slow camera orbit
    """
    
    def __init__(self, width, height, n_particles=2000):
        """
        Initialize particle field.
        
        Args:
            width: Window width
            height: Window height
            n_particles: Number of particles (1000-3000 recommended)
        """
        if not OPENGL_AVAILABLE:
            raise ImportError("PyOpenGL not available")
        
        self.width = width
        self.height = height
        self.n_particles = n_particles
        
        # Particle positions (random cloud)
        self.positions = np.random.randn(n_particles, 3).astype(np.float32)
        self.positions *= 5.0  # Spread out in 3D space
        
        # Animation state
        self.time = 0.0
        self.camera_angle = 0.0
        
        # Audio-reactive parameters
        self.beat_hz = 10.0
        self.carrier_hz = 200.0
        self.rms = 0.5
        
        # FPS tracking for dynamic particle scaling
        self.fps = 60.0
        
        # VBO for efficient rendering
        self.vbo = None
        
        self._init_gl()
    
    def _init_gl(self):
        """Initialize OpenGL state."""
        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        
        # Enable blending for transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Enable point sprites for particles (LARGE for visibility)
        glEnable(GL_POINT_SMOOTH)
        glPointSize(10.0)
        
        # Set up perspective projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = self.width / self.height
        gluPerspective(60.0, aspect, 0.1, 100.0)
        
        glMatrixMode(GL_MODELVIEW)
        
        # Clear color (lighter background for visibility)
        glClearColor(0.1, 0.1, 0.15, 1.0)
        
        # Create VBO for particle positions (much faster than immediate mode)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.positions.nbytes, self.positions, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
    
    def update(self, dt, beat_hz, carrier_hz, rms):
        """
        Update visualization state.
        
        Args:
            dt: Time delta (seconds)
            beat_hz: Current beat frequency (0-40 Hz)
            carrier_hz: Current carrier frequency (20-1000 Hz)
            rms: Current RMS amplitude (0-1)
        """
        self.time += dt
        self.beat_hz = beat_hz
        self.carrier_hz = carrier_hz
        self.rms = rms
        
        # Slow camera orbit
        self.camera_angle += dt * 5.0  # 5 degrees per second
    
    def render(self):
        """Render the particle field."""
        # Clear buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Set up camera
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Camera position (orbit around origin)
        cam_radius = 20.0
        cam_x = cam_radius * np.cos(np.radians(self.camera_angle))
        cam_z = cam_radius * np.sin(np.radians(self.camera_angle))
        cam_y = 5.0
        
        gluLookAt(
            cam_x, cam_y, cam_z,  # Eye position
            0.0, 0.0, 0.0,         # Look at center
            0.0, 1.0, 0.0          # Up vector
        )
        
        # Calculate pulse scale from beat
        pulse = 0.5 + 0.5 * np.sin(2.0 * np.pi * self.beat_hz * self.time)
        base_scale = 0.3 + 0.7 * pulse
        
        # Map carrier to hue (20 Hz → 0.6 (blue), 1000 Hz → 0.0 (red))
        hue = 0.6 - (self.carrier_hz - 20.0) / 980.0 * 0.6
        hue = np.clip(hue, 0.0, 0.6)
        
        # Brightness - MAXIMUM for visibility
        brightness = 1.0  # Full brightness always
        
        # Convert HSV to RGB
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, brightness)
        
        # Calculate alpha - MAXIMUM for visibility
        alpha = 1.0
        
        # Render particles using VBO (much faster than immediate mode)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, None)
        
        # Set uniform color (for MVP we use same color for all particles)
        glColor4f(r, g, b, alpha)
        
        # Draw all particles in one call (5-10x faster than glBegin/glEnd loop)
        glDrawArrays(GL_POINTS, 0, self.n_particles)
        
        glDisableClientState(GL_VERTEX_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
    
    def resize(self, width, height):
        """Handle window resize."""
        self.width = width
        self.height = height
        
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = width / height
        gluPerspective(60.0, aspect, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
    
    def adjust_particle_count(self, fps):
        """
        Dynamically adjust particle count based on FPS.
        
        Args:
            fps: Current FPS
        """
        self.fps = fps
        
        # If FPS drops below 50, reduce particles
        if fps < 50 and self.n_particles > 500:
            new_count = int(self.n_particles * 0.9)
            self.n_particles = max(500, new_count)
            # Regenerate positions
            self.positions = np.random.randn(self.n_particles, 3).astype(np.float32)
            self.positions *= 5.0
            # Update VBO
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, self.positions.nbytes, self.positions, GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
        
        # If FPS is high, can increase particles
        elif fps > 70 and self.n_particles < 3000:
            new_count = int(self.n_particles * 1.1)
            self.n_particles = min(3000, new_count)
            self.positions = np.random.randn(self.n_particles, 3).astype(np.float32)
            self.positions *= 5.0
            # Update VBO
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, self.positions.nbytes, self.positions, GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)


def is_opengl_available():
    """Check if OpenGL is available."""
    return OPENGL_AVAILABLE

