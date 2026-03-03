# Open Source Virtual Hand Calculator

Accessibility-first virtual calculator controlled by hand tracking.

## v1 Release
- Version: `v1.0.0`
- Release notes: [RELEASE_NOTES_v1.md](RELEASE_NOTES_v1.md)

## Fixed Python Version
- Project runtime is fixed to **Python `3.11.9`**
- File: `.python-version`

## One-Click Run

```bash
bash run.sh
```

What `run.sh` does:
1. Uses `python3.11` (falls back to `python3` if not available)
2. Creates `.venv` if needed
3. Installs dependencies from `requirements.txt`
4. Starts `hand_calculator_v2.py`

## Manual Run (Optional)

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python hand_calculator_v2.py
```

## Core Features (v1)
- Tremor-friendly hover+dwell input
- Startup calibration (30s) with saved per-user config
- Accessibility toggles:
  - Large Keys
  - High Contrast
  - Slow Mode
- Live tuning hotkeys:
  - `[` / `]` adjust dwell time
  - `-` / `=` adjust cooldown
- Safe math evaluator (`ast`-restricted, no raw `eval`)
- Session logs for tuning in `logs/*.jsonl`
- Camera robustness warnings + tracking confidence

## Runtime Controls
- `q`: quit
- `c`: clear
- `d`: delete
- `l`: toggle large keys
- `h`: toggle high contrast
- `m`: toggle slow mode

## Tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Project Structure

```text
auto_hand_calculator/
  hand_calculator_v2.py
  run.sh
  requirements.txt
  .python-version
  RELEASE_NOTES_v1.md
  tests/
  data/
  models/
  logs/
```
