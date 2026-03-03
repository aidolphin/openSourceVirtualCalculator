# Open Source Virtual Hand Calculator

This project is an open source calculator controlled by hand and index finger.
The goal is reliable input for users with hand shake/tremor and touch difficulty.

## Vision

Build a full virtual calculator model that works across devices:
- laptop camera
- phone camera
- tablet camera
- smart display / kiosk camera

Long-term goal: a complete open source hand-interaction engine for math input.

## Project Status (March 2026)

Current version:
- real-time hand tracking with MediaPipe
- virtual calculator UI
- dwell/hover based key press logic
- tremor-friendly tuning (smoothing, cooldown, key padding)

## Open Source + Income Plan

This project is open source first.

Future income plan:
- optional ad-supported app release
- optional pro hosted features

Core model commitment:
- core calculator interaction logic stays open source
- research updates and model improvements remain public

## Quick Start

```bash
pip install -r requirements.txt
python hand_calculator_v2.py
```

Shortcut:
```bash
bash run.sh
```

## How To Use

1. Show your index finger to the camera.
2. Move over a button.
3. Hold for a short time to activate the key.
4. Watch key color and hold progress feedback.

Keyboard controls:
- `q`: quit
- `c`: clear expression
- `d`: delete last character

## Research Roadmap (Simple)

Phase 1: Stable calculator baseline (now)
- improve tremor handling
- reduce false key presses
- improve hover UX feedback

Phase 2: Full math calculator model
- dataset for numbers, symbols, and gestures
- expression parser safety and advanced math functions
- confidence scoring per press

Phase 3: Multi-device virtual input
- camera calibration per device type
- low-light and low-end camera robustness
- latency optimization

Phase 4: Open model release
- publish trained checkpoints
- publish evaluation reports
- publish reproducible training scripts

## Suggested Timeline

- March-April 2026: finish robust input + test protocol
- May-June 2026: build and test full math input stack
- July-September 2026: train/evaluate larger model versions
- October-December 2026: open model release v1 + public demo

## What You Should Do For Research

1. Define exact success metrics.
   Example: key accuracy, false press rate, press latency, tremor-user success rate.
2. Collect data from real usage sessions.
   Record shaky and non-shaky hand sessions with consent.
3. Create train/val/test splits.
   Keep user-independent test set for fair measurement.
4. Build a benchmark script.
   One command to report metrics every time.
5. Iterate in small cycles.
   Tune one parameter at a time and compare results.
6. Publish transparent reports.
   Share failures, not only best numbers.

## Data Plan For Full Math Model

Include samples for:
- digits: `0-9`
- symbols: `+ - * / . =`
- actions: `DEL`, `C`
- transitions between nearby keys
- heavy tremor, mild tremor, no tremor
- different camera angles and lighting

## Repository Structure

```text
auto_hand_calculator/
  hand_calculator_v2.py
  run.sh
  requirements.txt
  README.md
  data/
  models/
```

## Contributing

Contributions are welcome:
- bug fixes
- model training scripts
- dataset tooling
- evaluation scripts
- accessibility testing

Open an issue with:
- problem description
- video or screenshot
- system info
- expected vs actual behavior

## Support

If you want to support this research:
- share feedback videos
- contribute code or data tools
- sponsor future compute/data cost

This project is being built for practical accessibility and open science.

