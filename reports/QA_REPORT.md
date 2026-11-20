# Export QA results

All checks below were executed against the final MP4 files.

| File | Result | Duration | Video | Audio | Loudness | Peak |
|---|---:|---:|---|---|---:|---:|
| output/01_construction_progress.mp4 | PASS | 18.000s | h264 1080×1920 yuv420p | aac 48000 Hz / 2 ch | -15.0 LUFS | -1.2 dBFS |
| output/02_construction_safety.mp4 | PASS | 21.000s | h264 1080×1920 yuv420p | aac 48000 Hz / 2 ch | -15.4 LUFS | -1.4 dBFS |
| output/03_before_after_transformation.mp4 | PASS | 17.000s | h264 1080×1920 yuv420p | aac 48000 Hz / 2 ch | -14.9 LUFS | -1.4 dBFS |

Each file also passed full decode, fast-start placement, audio/video duration matching, and black-frame, freeze and silence scans. Detector event arrays are empty in the JSON report.

Visual checks were completed from full-resolution preview frames, contact sheets, and a dedicated first-three-seconds sheet for the comparison edit.
