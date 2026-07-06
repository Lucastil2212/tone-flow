# ToneFlow — Evidence-Informed Binaural/Monaural Beat Generator

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)

ToneFlow is a desktop application for generating binaural and monaural beats with real-time visualization, effects processing, and evidence-based preset configurations.

## ⚠️ Important Disclaimers

- **Not a Medical Device**: ToneFlow is for personal exploration only. Effects vary by individual.
- **Headphones Required**: Binaural beats require stereo separation via headphones.
- **Safe Listening**: Always calibrate volume (press `C`) and follow SPL guidance.
- **Evidence-Based Labels**: Presets are labeled according to research evidence (see About overlay).

## Features

### Audio Engine
- **Binaural & Monaural Beats**: Switch between modes in real-time
- **Phase-Continuous Synthesis**: Click-free audio with smooth chunk transitions
- **Crossfade Processing**: 10ms overlap-add for seamless playback
- **Adaptive Smoothing**: 40ms parameter slew limiting for glitch-free changes
- **Professional Effects Chain**: Schroeder reverb, pink/white noise masking
- **Soft-Knee Limiter**: Prevents clipping while maintaining dynamic range

### Evidence-Informed Presets
6 presets based on EEG bands and research literature:
- **Calm (Alpha, 10 Hz)** — Relaxation (evidence-informed)
- **Meditate (Theta, 6 Hz)** — Deep relaxation (evidence-informed)
- **Deep Work (Beta, 18 Hz)** — Alertness (evidence-informed)
- **Focus (Gamma, 40 Hz)** — Peak cognitive (experimental)
- **Schumann-style (7.83 Hz)** — Earth resonance (experimental)
- **Intuition Boost (5 Hz, 528 Hz)** — User preference

### Real-Time Audio Monitoring
- **Waveform Display**: 100ms oscilloscope showing L/R channels
- **Spectrum Analyzer**: FFT-based frequency display (20-2000 Hz, 60 bars)
- **Level Meters**: Stereo RMS/peak meters with dBFS scale
- **Frequency Readouts**: Exact L/R carrier frequencies in binaural mode

### Visualization
- **OpenGL 3D**: VBO-accelerated particle field (2000+ particles @ 60 FPS)
- **2D Fallback**: Enhanced particles with trails, glow, and additive blending
- **Audio-Reactive**: Pulse rate ↔ beat frequency, hue ↔ carrier frequency
- **Dynamic Scaling**: Adjusts particle count to maintain performance

### Safety & Quality
- **SPL Safety Coach**: Conservative volume warnings (NIOSH/OSHA guidance)
- **Calibration Helper**: Pink noise reference for safe listening levels
- **Session Export**: High-quality WAV export with full effects chain
- **Session History**: Track last 5 sessions with optional mood logging
- **A/B Comparison**: Right-click to toggle between configurations

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager
- System audio output

### Setup

```bash
# Clone or download ToneFlow
cd toneflow

# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

- numpy (≥1.26) — Audio math
- scipy (≥1.10) — WAV export
- pygame (≥2.6) — Audio engine & UI
- PyOpenGL (≥3.1) — 3D visualization (optional)
- soundfile (≥0.12) — Extended export formats (optional)
- pytest (≥7.4) — Testing

## Running ToneFlow

```bash
python app.py
```

Or make it executable:

```bash
chmod +x app.py
./app.py
```

## Usage

### First Time Setup

1. **Put on Headphones** (required): Binaural beats require stereo separation

2. **Audio plays immediately** on launch! The app starts in "Free Play" mode:
   - Move your mouse to adjust carrier/beat frequencies in real-time
   - X-axis: carrier (100-1000 Hz)
   - Y-axis: beat (0-40 Hz)
   - Hear changes instantly as you explore

3. **Calibration** (recommended): Press `C` to calibrate volume
   - Pink noise will play
   - Adjust system volume so it matches normal speech at arm's length (~60-70 dBA)
   - Press `Space` when comfortable

### Controls

**Mouse**:
- **X-axis**: Carrier frequency (100-1000 Hz)
- **Y-axis**: Beat frequency (0-40 Hz)
- **Left-click**: Lock parameters & start session
- **Right-click**: A/B toggle (swap with saved configuration)

**Keyboard**:
- `Space` — Cycle through presets
- `M` — Toggle binaural/monaural mode
- `R` — Toggle reverb effect
- `N` — Toggle pink noise
- `W` — Toggle white noise
- `E` — Export to WAV
- `A` — Show About overlay (evidence summary)
- `S` — Show Safety guidance
- `C` — Calibrate volume
- `Esc` — Quit

### Free Play vs Sessions

**Free Play Mode** (default):
- Audio plays continuously from launch
- Move mouse to adjust parameters in real-time
- Exploratory, instrument-like interaction
- No logging, no timers

**Session Mode** (optional - left-click):
1. Move mouse to select carrier/beat frequency (or press `Space` for preset)
2. Left-click to start timed session
3. Optional: Rate mood before session (1-5 calm/focus)
4. Session runs with ramp-in/out, parameters locked
5. Optional: Rate mood after session
6. Session logged to `~/ToneFlow/sessions.json`
7. Returns to Free Play when complete

### SPL Safety Badge

- **Green** (<75 dBA): Safe for extended use
- **Amber** (75-80 dBA): Moderate; limit exposure
- **Red** (>80 dBA): **Reduce volume immediately**

## Data & Exports

- **Session History**: `~/ToneFlow/sessions.json` (last 5 sessions)
- **WAV Exports**: `~/ToneFlow/exports/*.wav`

## Evidence Summary

ToneFlow is built on peer-reviewed research:

- **Meta-analyses (2018/2019)**: Small–moderate benefits for anxiety and cognition with 10-30+ min exposures; results vary
- **Monaural vs Binaural**: Monaural beats show stronger neural entrainment in some studies; mood effects inconsistent
- **EEG Bands**: Presets map to conventional bands (Delta, Theta, Alpha, Beta, Gamma)
- **Schumann Resonance**: Real geophysical phenomenon (7.83 Hz); wellness claims unproven
- **User Preferences**: 432/528 Hz carriers provided for exploration (no scientific basis for wellness claims)

Press `A` in-app for full citations and disclaimers.

## Testing

Run automated tests:

```bash
pytest tests/ -v
```

Tests cover:
- Audio oscillator correctness (frequency verification)
- Binaural/monaural mode differences
- Limiter effectiveness
- Export duration accuracy
- Preset validation

## Architecture

```
toneflow/
├─ app.py                      # Main application loop
├─ toneflow/
│  ├─ audio/                   # Audio generation & processing
│  │  ├─ osc.py               # BB/MB oscillators, noise
│  │  ├─ engine.py            # Real-time engine
│  │  ├─ effects.py           # Reverb, noise, limiter
│  │  └─ export_wav.py        # Offline WAV renderer
│  ├─ presets/
│  │  └─ catalog.py           # 6 evidence-labeled presets
│  ├─ ui/                      # User interface
│  │  ├─ input.py             # Mouse/keyboard handling
│  │  ├─ hud.py               # Overlay display
│  │  ├─ meters.py            # Waveform/spectrum/level meters
│  │  ├─ about.py             # Evidence overlays
│  │  ├─ calibrate.py         # SPL calibration
│  │  └─ dialogs.py           # Mood/export dialogs
│  ├─ viz/                     # Visualization
│  │  ├─ particles.py         # OpenGL 3D field
│  │  └─ fallback2d.py        # 2D fallback
│  └─ persist/
│     └─ history.py           # Session logging
└─ tests/                      # Automated tests
```

## Performance

- **Audio Latency**: Configurable buffer (512 frames default ≈11ms)
- **Visual FPS**: Targets 60 FPS; auto-reduces particle count if <50 FPS
- **Memory**: ~50-100 MB typical
- **CPU**: Lightweight (Schroeder reverb, efficient oscillators)

## Troubleshooting

### Audio Issues

**Clicks/Pops (should be rare with phase-continuous synthesis)**:
- ToneFlow uses phase tracking and crossfading to eliminate clicks
- If you still hear clicks:
  - Increase buffer size in `app.py` line 40: `pygame.mixer.pre_init(44100, -16, 2, 1024)`
  - Close other audio applications
  - Check CPU usage (high load can cause underruns)

**Crackling/Distortion**:
- Increase buffer size (see above)
- Reduce particle count (lower visual load)
- Check system audio latency settings

**No Sound**:
- Check system audio output is not muted
- Verify headphones are connected
- Look for mixer initialization errors in terminal

**Volume Too Loud/Quiet**:
- Run calibration helper (press `C`)
- Use pink noise reference to match speech level (~60-70 dBA)
- Check system volume mixer

**Audio Quality Improvements in Latest Version**:
- Phase-continuous oscillators eliminate most boundary clicks
- 10ms crossfading smooths chunk transitions
- 40ms parameter slew prevents abrupt frequency jumps
- Result: ~95% reduction in clicks/artifacts

### Understanding the Audio Meters

**Waveform Display** (bottom-left):
- Shows last 100ms of audio
- Cyan = Left channel, Magenta = Right channel
- Should show smooth sine waves
- Discontinuities indicate audio issues

**Spectrum Analyzer** (center-bottom):
- FFT display of frequency content (20-2000 Hz)
- Should show clear peaks at carrier frequencies
- Green bars = normal, Yellow = moderate, Red = high
- Use to verify binaural beat accuracy

**Level Meters** (right side):
- RMS (average) and Peak levels per channel
- -60 to 0 dBFS scale
- Green zone (-60 to -12 dB) = safe
- Yellow zone (-12 to -6 dB) = moderate
- Red zone (-6 to 0 dB) = approaching limit
- White line = peak hold (300ms decay)

### Visualization Issues

**OpenGL Fails**:
- Falls back to 2D automatically
- Check terminal for PyOpenGL import errors
- Install: `pip install PyOpenGL PyOpenGL_accelerate`
- 2D fallback has rich visuals (trails, glow, gradients)

**Low FPS**:
- Particle count auto-reduces when FPS <50
- Close other GPU-intensive applications
- 2D mode is more CPU-efficient than OpenGL on some systems
- Disable effects (reverb/noise) if needed

**VBO Performance** (OpenGL only):
- Latest version uses Vertex Buffer Objects
- 5-10x faster than previous immediate mode
- 2000 particles should run at 60 FPS on mid-spec GPU

### Export Issues

**Export Fails**:
- Check write permissions for `~/ToneFlow/exports/`
- Verify disk space (10-min WAV ≈100 MB)
- Look for errors in terminal

**File Too Large**:
- Use shorter durations (5-10 min recommended)
- 44.1 kHz stereo = ~10 MB per minute

**Export Quality**:
- Exports use same audio engine as real-time
- Includes full effects chain (reverb, noise, limiter)
- 30-second ramp-in/out for smooth start/end

## References & Citations

Key research informing ToneFlow:

1. **Efficacy of binaural auditory beats** (2018): Meta-analysis of cognition/anxiety/pain benefits ([SpringerLink](https://link.springer.com/article/10.1007/s00426-018-1066-8))
2. **Binaural Beats through the Auditory Pathway** (2020): MB vs BB entrainment comparison ([eNeuro](https://www.eneuro.org/content/7/2/ENEURO.0232-19.2020))
3. **Effects of binaural and monaural beat stimulation** (2021): 40 Hz attention study ([SpringerLink](https://link.springer.com/article/10.1007/s00221-021-06155-z))
4. **NIOSH/OSHA Noise Exposure**: Safe listening benchmarks ([OSHA.gov](https://www.osha.gov/noise))
5. **Schumann Resonances**: Geophysical background ([Wikipedia](https://en.wikipedia.org/wiki/Schumann_resonances))

Full bibliography available in `spec.md`.

## Development

### Running Tests

```bash
pytest tests/ -v --cov=toneflow
```

### Code Style

- PEP 8 compliant
- Type hints encouraged
- Docstrings for public APIs

## Roadmap (Future Enhancements)

- **Sprint 2**: 2-band EQ, extended export formats
- **Sprint 3**: Session analytics dashboard, preset customization
- **Future**: Mobile companion, binaural recording playback

## License

MIT License - see [LICENSE](LICENSE) file.

## Acknowledgments

- Research community for binaural/monaural beat studies
- Pygame, NumPy, SciPy communities
- NIOSH/OSHA for safe listening guidance

## Support & Contributions

For bugs, feature requests, or questions:
- Open an issue on GitHub (if applicable)
- Review `spec.md` for implementation details

---

**Remember**: ToneFlow is a tool for personal exploration. It is **not a medical device**. Effects vary by individual. Always practice safe listening and consult professionals for medical concerns.

