# ToneFlow — Complete Implementation Blueprint (Desktop Python MVP)

This document contains **everything** needed to build ToneFlow end-to-end: scientific rationale, features, UX, architecture, dependencies, data contracts, implementation details, and QA. Citations are included at all load-bearing points.

---

## 1) Scientific basis & safety (what we claim, and what we don’t)

* **What binaural beats are.** A perceptual “third tone” created when two slightly different frequencies are presented separately to each ear; perceived beat = **frequency difference**. ([SpringerLink][1])
* **Evidence overview.** A 2018/2019 meta-analysis found **small–moderate** benefits across anxiety, pain, memory/attention when protocols use appropriate beat frequency and adequate exposure (often 10–30+ min). Later reviews highlight **mixed** entrainment results and variability across studies/designs. We will position effects as **possible** and **user-dependent**. ([SpringerLink][1])
* **Monaural vs binaural.** An eNeuro study comparing **binaural beats (BB)** and **monaural beats (MB)** found **stronger neural entrainment** with MB at some levels, while mood effects were inconsistent; therefore we include MB as a first-class toggle for A/B comparisons. ([eNeuro][2])
* **EEG bands used for presets.** Delta (0.5–4 Hz), Theta (4–8 Hz), Alpha (8–12 Hz), Beta (13–30 Hz), Gamma (≥30 Hz). These are standard bands that inform our “Relax/Meditate/Focus” presets; this is **conventional mapping**, not a guarantee of effect. ([CDC][3])
* **Schumann note.** The **7.83 Hz** geophysical resonance of the Earth–ionosphere cavity is real physics; any wellness link is **unproven**. We label this preset **experimental**. ([Wikipedia][4])
* **Noise/Masking.** Pink noise (energy per octave) is often comfortable for masking; cognitive impacts are mixed, so we present it as a **comfort/masking** layer rather than a cognition enhancer. ([WIRED][5])
* **Safe listening.** We follow NIOSH/OSHA guidance: **85 dBA over 8 h** as the key benchmark; include an **SPL coach** that warns conservatively at ~80 dBA-equivalent with a simple RMS→A estimate and a **speech-at-arm’s-length** heuristic cue. ([OSHA][6])

**Bottom line for copy:** “Evidence-informed, results vary; not a medical device.”

---

## 2) Functional scope

### 2.1 Audio generation & modes

* **Sample rate/format:** 44.1 kHz, 16-bit stereo (float pipeline → int16 out).
* **Carriers:** sweepable **100–1000 Hz** (comfortable, widely used range). ([SpringerLink][1])
* **Beat frequency:** **0–40 Hz** (clamped).
* **Modes:**

  * **Binaural beats (BB)** — separate L/R carriers with ±Δ/2.
  * **Monaural beats (MB)** — sum of two nearby sines; same for L/R (A/B against BB). ([eNeuro][2])
* **Session timing:** **5 / 10 / 15 / 20 / 30 min** + “No limit”; ramp-in/out 30–60 s.
* **Smoothing:** parameter slew limiter (≈10–50 ms) + short **cross-fade** between **50–100 ms** audio chunks to avoid clicks.
* **Limiter:** soft-knee peak limiter to −1 dBFS.

### 2.2 Effects (modular chain)

* **Reverb (optional):** lightweight Schroeder/FDN or short IR convolution (0.3–0.7 s); wet/dry 0–100%.
* **Noise (optional):** **pink** (preferred default) and **white**; level −30…−6 dBFS; labeled “Comfort/Masking”.
* **2-band EQ (optional):** gentle low/high shelves for timbre comfort.
* **Chain is pluggable** so you can add future effects without touching the engine.

### 2.3 Presets (evidence-forward labels)

| Preset           |    Beat | Duration (default) | Carrier default | Mode                   | Label                                                         |
| ---------------- | ------: | -----------------: | --------------: | ---------------------- | ------------------------------------------------------------- |
| Calm (Alpha)     |   10 Hz |             15 min |          512 Hz | BB (MB toggle)         | *evidence-informed* (relaxation). ([SpringerLink][1])         |
| Meditate (Theta) |    6 Hz |             20 min |          440 Hz | BB                     | *evidence-informed* (deeper relaxation). ([ScienceDirect][7]) |
| Deep Work (Beta) |   18 Hz |             15 min |          500 Hz | BB/MB                  | *evidence-informed* (alertness). ([ScienceDirect][7])         |
| Focus (Gamma)    |   40 Hz |          10–15 min |          600 Hz | BB/MB (+optional pink) | *experimental focus* (mixed). ([SpringerLink][8])             |
| Schumann-style   | 7.83 Hz |             20 min |          432 Hz | BB                     | *experimental / Earth resonance*. ([Wikipedia][4])            |
| Intuition Boost  |  4–6 Hz |             20 min |          528 Hz | BB                     | *user preference / not evidence-based*.                       |

> **User-preference carriers** (432/528 Hz) are surfaced with a clear disclaimer.

### 2.4 Interaction model (mouse-first, minimal UI)

* **Fullscreen canvas** with OpenGL visual:

  * **X-axis:** carrier (100–1000 Hz)
  * **Y-axis:** beat (0–40 Hz)
* **Left-click:** lock & start session (uses current preset duration + ramp-in).
* **Right-click:** quick **A/B** toggle (current vs saved slot).
* **Keys:**
  `Space` presets • `M` mono/binaural • `R` reverb • `N/W` noise • `E` export WAV • `L` load recent • `A` About overlay • `C` Calibration • `S` Safety overlay • `Esc` quit.

### 2.5 Visualization (OpenGL particle field)

* ~1–5k particles (dynamic scaler).
* **Pulse rate ~ beat**, **hue ~ carrier**, **bloom/scale ~ RMS**.
* Camera slow-orbit; fallback to **2D Pygame** if OpenGL unavailable. ([pyopengl.sourceforge.net][9])

### 2.6 Export & persistence

* **WAV export** (5/10/20 min; 44.1 kHz, 16-bit) using SciPy **wavfile.write** or `soundfile` (libsndfile) for broader formats. ([SciPy Documentation][10])
* **Session history** (ring buffer last 5): preset, carrier, beat, effects, duration, timestamp, optional mood pre/post.
* **Local-only** data path: `~/ToneFlow/` (`sessions.json`, `exports/`).

### 2.7 Safety & calibration

* **Headphone reminder** (beats require stereo separation).
* **SPL coach:** HUD badge Green <75, Amber 75–80, Red >80 dBA-equiv; tooltip uses **NIOSH/OSHA** and **speech-at-arm’s-length** heuristics. ([OSHA][6])
* **Calibration helper:** plays **pink noise** (speech-like band) with instructions to set device volume such that **normal speech at arm’s length is clear** (~60–70 dBA). ([CDC][3])

---

## 3) Non-functional targets

* **Audio latency:** configurable buffer; default **256–512 frames**; smaller = less lag per Pygame docs. Expose “Latency” in Settings. ([Pygame][11])
* **Visual performance:** 60 FPS on mid-spec; auto-reduce particle count if <50 FPS.
* **Stability:** limiter prevents clipping; crossfades prevent zipper/clicks.
* **Portability:** Windows/macOS/Linux (Python 3.10+).

---

## 4) Architecture & project structure

```
toneflow/
├─ app.py                      # main loop & dependency wiring
├─ requirements.txt            # pinned libs
├─ README.md                   # quick start
├─ LICENSE
├─ toneflow/
│  ├─ audio/
│  │  ├─ osc.py               # sine generators, pink/white noise
│  │  ├─ engine.py            # double-buffer loop, smoothing, limiter, SPL est.
│  │  ├─ effects.py           # reverb, EQ, noise, chain registry
│  │  └─ export_wav.py        # offline renderer (SciPy/soundfile)
│  ├─ presets/
│  │  └─ catalog.py           # preset definitions + labels/caveats
│  ├─ ui/
│  │  ├─ input.py             # mouse/keys mapping
│  │  ├─ hud.py               # HUD badges, timers, warnings
│  │  ├─ about.py             # evidence copy & links
│  │  ├─ dialogs.py           # pygame_gui popups (export chooser, mood sliders)
│  │  └─ calibrate.py         # pink-noise calibration flow
│  ├─ viz/
│  │  ├─ particles.py         # OpenGL field
│  │  └─ fallback2d.py        # simple 2D viz
│  └─ persist/
│     └─ history.py           # JSON ring-buffer + mood logs
└─ tests/
   ├─ test_audio_engine.py
   ├─ test_export.py
   └─ test_presets.py
```

**Key internal contracts**

* **Preset object**

  ```json
  {
    "id": "alpha_calm_10hz",
    "label": "Calm (Alpha, 10 Hz)",
    "beat_hz": 10.0,
    "carrier_hz_default": 512.0,
    "duration_min_default": 15,
    "tags": ["evidence-informed"],
    "disclaimer": "Effects vary; not a medical device."
  }
  ```

* **Session log entry**

  ```json
  {
    "ts": "2025-10-19T15:23:00Z",
    "preset_id": "alpha_calm_10hz",
    "carrier_hz": 512.0,
    "beat_hz": 10.0,
    "mode": "binaural",
    "effects": {"reverb_wet": 0.35, "noise": {"type":"pink","level_dbfs":-20}, "eq":{"low_shelf_db":-2,"high_shelf_db":+2}},
    "duration_sec": 900,
    "mood_pre": {"calm": 2, "focus": 2},
    "mood_post": {"calm": 4, "focus": 3}
  }
  ```

---

## 5) Detailed implementation notes

### 5.1 Audio engine

* Initialize mixer at app start:

  ```python
  pygame.mixer.pre_init(44100, -16, 2, buffer)  # buffer 256–512 default
  pygame.init()
  ```

  Pygame docs: **smaller buffer reduces lag**; let user pick if crackle occurs. ([Pygame][11])

* **Chunk synthesis (per 50–100 ms):**

  * Generate time vector `t` for the chunk.
  * **BB:** left = sin(2π*(base−Δ/2)*t), right = sin(2π*(base+Δ/2)*t).
  * **MB:** mono = sin(2π*(base−Δ/2)*t) + sin(2π*(base+Δ/2)*t); duplicate to L/R. ([eNeuro][2])
  * Apply **slew limiter** (exponential smoothing) to avoid abrupt jumps.
  * Process through **effects chain**; apply **limiter**; convert float → int16.

* **SPL estimation (rough):**
  `rms = sqrt(mean(x**2)); dBFS = 20*log10(rms)` then map to approximate **dBA** with a fixed offset determined during calibration (pink noise step). Show **badges** based on thresholds 75/80 dB equivalents. (We explicitly state it’s an estimate.) ([OSHA][6])

### 5.2 Effects

* **Pink noise** via filtering white noise with 1/f tilt (IIR) or Voss algorithm; level set in **dBFS**.
* **Reverb**: Schroeder (comb + allpass) for CPU-light implementation; alternative: convolve with short exponential-decay IR (SciPy `signal.fftconvolve`) for subtle ambience.
* **EQ**: two shelving biquads (low shelf at ~200 Hz, high shelf at ~4–6 kHz; ±6 dB range).

### 5.3 Visualization

* **PyOpenGL** setup (GL 2.1): perspective cam, depth test, VBO with particle positions; hue mapped from carrier (100→blue, 1000→red), pulse via `sin(beat*t)` scaling. Fallback uses Pygame 2D if import fails. ([pyopengl.sourceforge.net][9])

### 5.4 UI & dialogs

* Use **pygame_gui** for overlays/popups (export duration, mood sliders, calibration prompts). ([Pygame GUI Documentation][12])

### 5.5 Export

* **Default:** 10-minute WAV with current chain and limiter.
* Use **SciPy wavfile.write** (simple PCM) or **soundfile** for extended formats/floting-point. ([SciPy Documentation][10])

---

## 6) UX copy (ready to paste)

**About (toggle with `A`):**
“ToneFlow uses binaural beats (an auditory illusion; beat = L/R frequency difference). Some studies and meta-analyses report small–moderate benefits for anxiety and aspects of cognition with **10–30+ min** exposures; results vary by protocol and listener. Monaural beats can show stronger neural entrainment in some studies, but mood effects are inconsistent. The **Schumann 7.83 Hz** preset reflects a geophysical resonance; wellness claims are unproven. 432/528 Hz carriers are provided as user preferences. Headphones required.” ([SpringerLink][1])

**Safety (Settings + `S` tooltip):**
“Following NIOSH/OSHA guidance: 85 dBA (8 h) is a key exposure benchmark. We warn near **80 dBA-equivalent** (estimate). Lower volume until normal speech at arm’s length is clear.” ([OSHA][6])

**Preset disclaimers (inline):**

* Calm/Meditate/Deep Work: “Evidence-informed; effects vary.” ([SpringerLink][1])
* Focus (Gamma): “Experimental focus (mixed evidence).” ([SpringerLink][8])
* Schumann-style: “Experimental / Earth resonance (no proven wellness effect).” ([Wikipedia][4])
* Intuition Boost: “User preference / not evidence-based.”

---

## 7) Dependencies & versions

Create `requirements.txt`:

```
numpy>=1.26
scipy>=1.10
pygame>=2.6
PyOpenGL>=3.1
pygame_gui>=0.6.14
soundfile>=0.12   # optional, for extended export formats
```

* **Pygame mixer latency guidance** (smaller buffer → less lag). ([Pygame][11])
* **pygame_gui** docs & PyPI. ([Pygame GUI Documentation][12])
* **SciPy wavfile** docs for WAV export; **soundfile**/libsndfile for broader support. ([SciPy Documentation][10])

---

## 8) Build, run, and paths

**Install**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Run**

```bash
python app.py
```

**Data locations**

* Config & history: `~/ToneFlow/sessions.json`
* Exports: `~/ToneFlow/exports/*.wav`

---

## 9) Testing & QA

### 9.1 Automated

* **Engine:** unit test that BB @ (500 Hz, Δ=10) produces channels with expected instantaneous frequency and correct **beat diff**; MB path duplicates channel.
* **Limiter:** ensure peaks ≤ −1 dBFS after chain.
* **Export:** duration exactness; stereo shape `[N,2]`; file decodes correctly. ([SciPy Documentation][10])
* **Latency toggle:** change mixer buffer and confirm under-run free at default settings (allow user fallback).

### 9.2 Manual protocol checks

* **Headphone L/R test:** brief alternating pips to confirm stereo.
* **A/B comparisons:** BB vs MB at identical carrier/beat for 5–10 min each (Gamma 40 Hz and Alpha 10 Hz test tiles). Log mood (1–5 calm/focus) post-block; store locally. ([eNeuro][2])
* **Calibration:** pink noise prompt; verify SPL badge matches user’s comfortable speech level heuristic. ([CDC][3])

### 9.3 Performance

* Verify 60 FPS at 1k particles on mid-spec GPU; auto-reduce particle count if FPS <50.
* Check audio glitch-free at 256–512 buffer; if not, present **Latency** setting.

---

## 10) Risks & mitigations

* **Perceived effects vary / placebo confounds.** Provide A/B tools, logging, and **no over-promising** in copy. ([ScienceDirect][7])
* **Latency on some machines.** Expose buffer slider; document Pygame guidance. ([Pygame][11])
* **Loudness estimation error.** Calibrate using pink noise + heuristic; message it as **estimate**. ([CDC][3])
* **OpenGL availability.** Ship 2D fallback path; detect and downgrade gracefully. ([pyopengl.sourceforge.net][9])

---

## 11) Implementation roadmap (short sprints)

**Sprint 1 — Core audio + minimal UI (engine complete)**

* Mixer init + buffer size option; BB/MB oscillators, smoothing, limiter.
* Presets (6), timers with ramp-in/out, mouse X/Y mapping.
* 2D fallback viz + minimal HUD; WAV export (10 min default).
* History ring buffer.

**Sprint 2 — Effects + OpenGL viz**

* Reverb, pink/white noise, 2-band EQ; chain on/off.
* OpenGL particle field with beat-pulse and carrier-hue; dynamic particle scaler.

**Sprint 3 — Safety, calibration, and polish**

* SPL coach badges & tooltips, headphone reminder.
* Calibration helper; `pygame_gui` overlays (export chooser, mood sliders, About).
* A/B toggle and mood logging; error handling and settings panel.

---

## 12) Appendix — key references

* **Meta-analysis (2018/2019):** cognition/anxiety/pain, longer exposures help. ([SpringerLink][1])
* **Recent review:** entrainment evidence mixed across studies. ([ScienceDirect][7])
* **MB vs BB entrainment:** comparative human auditory pathway study. ([eNeuro][2])
* **40 Hz attention study (BB/MB/PN):** task outcomes vary by condition. ([SpringerLink][8])
* **NIOSH/OSHA noise & speech heuristic:** safe-listening benchmarks and practical cue. ([OSHA][6])
* **Schumann Resonance background (physics).** ([Wikipedia][4])
* **Pygame mixer latency guidance.** ([Pygame][11])
* **PyOpenGL docs & tutorial (for setup).** ([pyopengl.sourceforge.net][9])
* **WAV export docs (SciPy) & alt (soundfile).** ([SciPy Documentation][10])

---

### Done. This spec is self-contained and implementation-ready.

If you want, I can also generate a **scaffolded codebase** (folders, stubs, and TODOs) so you can `pip install -r requirements.txt` and start filling in modules immediately.

[1]: https://link.springer.com/article/10.1007/s00426-018-1066-8?utm_source=chatgpt.com "Efficacy of binaural auditory beats in cognition, anxiety, and pain ..."
[2]: https://www.eneuro.org/content/7/2/ENEURO.0232-19.2020?utm_source=chatgpt.com "Binaural Beats through the Auditory Pathway: From Brainstem to ... - eNeuro"
[3]: https://www.cdc.gov/niosh/noise/prevent/understand.html?utm_source=chatgpt.com "Understand Noise Exposure | Noise and Hearing Loss | CDC"
[4]: https://en.wikipedia.org/wiki/Schumann_resonances?utm_source=chatgpt.com "Schumann resonances"
[5]: https://www.wired.com/story/colours-of-noise?utm_source=chatgpt.com "White, pink, blue and violet: The colours of noise"
[6]: https://www.osha.gov/noise?utm_source=chatgpt.com "Occupational Noise Exposure - Overview | Occupational Safety and Health ..."
[7]: https://www.sciencedirect.com/org/science/article/pii/S1874944524001461?utm_source=chatgpt.com "Binaural Beats’ Effect on Brain Activity and ... - ScienceDirect"
[8]: https://link.springer.com/article/10.1007/s00221-021-06155-z?utm_source=chatgpt.com "Effects of binaural and monaural beat stimulation on attention and EEG ..."
[9]: https://pyopengl.sourceforge.net/documentation/?utm_source=chatgpt.com "PyOpenGL Documentation - SourceForge"
[10]: https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.wavfile.write.html?utm_source=chatgpt.com "write — SciPy v1.16.2 Manual"
[11]: https://www.pygame.org/docs/ref/mixer.html?utm_source=chatgpt.com "pygame.mixer — pygame v2.6.0 documentation"
[12]: https://pygame-gui.readthedocs.io/en/latest/?utm_source=chatgpt.com "Documentation - Home Page — Pygame GUI 0.6.14 documentation"

