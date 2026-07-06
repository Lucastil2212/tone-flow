#!/usr/bin/env python3
"""Verify ToneFlow installation and dependencies."""

import sys
from pathlib import Path

def check_module(name, required=True):
    """Check if a module can be imported."""
    try:
        __import__(name)
        print(f"✓ {name}")
        return True
    except ImportError as e:
        if required:
            print(f"✗ {name} - REQUIRED: {e}")
        else:
            print(f"⚠ {name} - optional: {e}")
        return False

def main():
    print("="*60)
    print("ToneFlow Installation Verification")
    print("="*60)
    print()
    
    print("Checking Python version...")
    version = sys.version_info
    if version >= (3, 10):
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Need 3.10+")
        return 1
    
    print()
    print("Checking required dependencies...")
    required = [
        'numpy',
        'scipy',
        'pygame',
    ]
    
    all_good = True
    for module in required:
        if not check_module(module):
            all_good = False
    
    print()
    print("Checking optional dependencies...")
    optional = [
        'OpenGL',
        'soundfile',
        'pytest',
    ]
    
    for module in optional:
        check_module(module, required=False)
    
    print()
    print("Checking ToneFlow modules...")
    toneflow_modules = [
        'toneflow.audio.osc',
        'toneflow.audio.engine',
        'toneflow.audio.effects',
        'toneflow.audio.export_wav',
        'toneflow.presets.catalog',
        'toneflow.ui.input',
        'toneflow.ui.hud',
        'toneflow.ui.about',
        'toneflow.ui.calibrate',
        'toneflow.ui.dialogs',
        'toneflow.viz.particles',
        'toneflow.viz.fallback2d',
        'toneflow.persist.history',
    ]
    
    for module in toneflow_modules:
        if not check_module(module):
            all_good = False
    
    print()
    print("="*60)
    if all_good:
        print("✓ All required dependencies installed!")
        print("  Run: python app.py")
    else:
        print("✗ Some dependencies missing")
        print("  Install: pip install -r requirements.txt")
    print("="*60)
    
    return 0 if all_good else 1

if __name__ == '__main__':
    sys.exit(main())

