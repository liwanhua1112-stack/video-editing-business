# Commercial delivery report

## Final exports

| Sample | Duration | File size | Visual structure | Export time |
|---|---:|---:|---|---:|
| Construction Progress | 18.000 s | 17,480,557 bytes | Five-stage timeline montage with directional transitions | 47.117 s |
| Construction Safety | 21.000 s | 16,492,216 bytes | Five-module field-safety checklist interface | 66.491 s |
| Before / After Transformation | 17.000 s | 10,804,196 bytes | Matched-view animated comparison sliders and reveal cuts | 104.570 s |

Export time is the measured successful FFmpeg encoding time on the current five-core cloud machine. Observed image-generation wall time was approximately 180.1 s, 210.2 s and 121.3 s respectively. The resulting measured generation-plus-export compute subtotals were approximately 227.2 s, 276.7 s and 225.9 s. These figures exclude creative direction, source-code authoring, failed setup probes and QA.

## Technical conformance

All three files use 1080×1920 progressive video at a constant 30 fps, H.264 High profile, yuv420p, 1:1 sample aspect ratio, AAC-LC audio at 48 kHz stereo, and front-loaded MP4 metadata for mobile streaming.

| Sample | Decode | Audio/video delta | Black events | Freeze events | Silence events | Integrated loudness | True peak |
|---|---:|---:|---:|---:|---:|---:|---:|
| Construction Progress | Pass | 0.000 s | 0 | 0 | 0 | −15.0 LUFS | −1.2 dBFS |
| Construction Safety | Pass | 0.000 s | 0 | 0 | 0 | −15.4 LUFS | −1.4 dBFS |
| Before / After Transformation | Pass | 0.000 s | 0 | 0 | 0 | −14.9 LUFS | −1.4 dBFS |

The automated validation record is in `reports/qa_results.json`. Full-resolution hero frames and contact sheets were inspected for subtitle spelling, safe-zone placement, image continuity, PPE presentation, transition frames and disclosure visibility.

## Requirement assessment

### Achieved

- Three actual MP4 deliverables within the requested duration ranges
- Three clearly different editing structures and graphic systems
- English captions with high-contrast typography and mobile-safe positioning
- Visible engineering progress from foundations to completed building
- Safety coverage including PPE, access routes, controlled lifting, communication and tool inspection
- Immediate Before / After split-screen hook from the first frame
- Animated camera pushes, pans, tilts, speed changes, wipes and matched-view slider reveals
- Original procedural soundtracks with section impacts, transitions and mastered loudness
- Persistent `AI-GENERATED CONCEPT • DEMO` labeling with no claim of real client work
- Reproducible renderer, included source assets and automated QA script

### Remaining improvements

- The source visuals are AI-generated still images. Camera movement is created in post through synchronized push, pan, tilt and reveal animation. It is not optical motion captured by a physical camera.
- The current samples demonstrate editing and motion-design capability. Replacing the concept images with licensed live-action source clips would better demonstrate subject motion, natural camera parallax, motion blur and production-sound editing.
- AI-generated workers, tools and building details were visually reviewed and no obvious high-impact defects were found in the selected frames. The safety sample is a portfolio concept and should not be used as regulatory training material.
- Playback was validated through full FFmpeg decode and frame inspection in this cloud environment. A physical iOS or Android device was not available for a final hardware-player check.

## Cost and authorization

Known direct procurement cost is US$0.00. No paid stock media, third-party recording or client footage was used. Visual use is subject to the image-generation service terms applicable to the user's account. Open Sans is used under Apache License 2.0. Audio is generated from code and contains no imported recordings.

## Commercial quality self-check

The three edits pass technical delivery checks and are visually coherent enough to demonstrate timing, graphic hierarchy, transitions, color treatment and sound design to prospective clients. The simulated source-material disclosure remains visible throughout. For proposals specifically requesting live-action construction experience, the samples should be presented as editing concept demos and supplemented with an authorized real-footage cut when source media becomes available.
