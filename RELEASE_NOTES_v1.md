# Release Notes v1.0.0 (March 2026)

## Highlights
- Tremor-friendly virtual hand calculator with dwell-based key activation.
- 30-second startup calibration with saved per-user settings (`config.json`).
- Accessibility toggles:
  - Large Keys
  - High Contrast
  - Slow Mode
- Live tuning hotkeys for dwell and cooldown.
- Safe math engine using restricted `ast` evaluation (no raw `eval`).
- Session telemetry logs for tuning (`logs/*.jsonl`).
- Camera robustness warnings:
  - low light warning
  - partial hand visibility warning
  - tracking confidence indicator

## Packaging
- One-click runnable launcher via `bash run.sh`.
- Fixed project Python version with `.python-version` set to `3.11.9`.

## Test Status
- Unit and regression test suite passing (`9/9`):
  - expression parsing
  - button action logic
  - hover/dwell transition behavior

## Known Limits
- Current UI is desktop camera oriented (single-camera setup).
- Advanced scientific functions UI is not yet exposed on virtual keys.
