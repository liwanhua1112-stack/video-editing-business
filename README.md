# Construction video editing portfolio

This project renders three vertical English-language construction portfolio samples. The included visuals are AI-generated concept images and every final video carries a persistent disclosure.

## Deliverables

- `output/01_construction_progress.mp4`
- `output/02_construction_safety.mp4`
- `output/03_before_after_transformation.mp4`
- Matching full-resolution preview JPG files in `previews/`

## Download

For the easiest phone download, use the compact 720p package or the individual files below. The 1080p masters remain in `output/`.

- [Download all three 720p videos (ZIP)](https://github.com/liwanhua1112-stack/video-editing-business/raw/refs/heads/main/delivery/video-editing-business-videos-720p.zip)
- [Construction Progress — 720p MP4](https://github.com/liwanhua1112-stack/video-editing-business/raw/refs/heads/main/delivery/mobile_720p/01_construction_progress_720p.mp4)
- [Construction Safety — 720p MP4](https://github.com/liwanhua1112-stack/video-editing-business/raw/refs/heads/main/delivery/mobile_720p/02_construction_safety_720p.mp4)
- [Before / After Transformation — 720p MP4](https://github.com/liwanhua1112-stack/video-editing-business/raw/refs/heads/main/delivery/mobile_720p/03_before_after_transformation_720p.mp4)

## Requirements

- Python 3.12
- NumPy 2.3.5
- FFmpeg and ffprobe 7.1 or later with libx264, AAC, libass and drawtext support
- Open Sans installed at `/usr/share/fonts/truetype/open-sans`

The current cloud environment already contains these dependencies. No network access is needed after checkout because all visual assets are included.

## Render

Run all three exports from the repository root.

```bash
python3 src/render_samples.py --sample all
```

Render one sample when iterating.

```bash
python3 src/render_samples.py --sample progress
python3 src/render_samples.py --sample safety
python3 src/render_samples.py --sample before-after
```

The renderer generates each procedural audio bed and subtitle track, then exports H.264/AAC MP4 with fast-start metadata.

## Validate

```bash
python3 src/qa_outputs.py
```

The validator performs full decode, stream and duration checks, black-frame, freeze and silence scans, loudness measurement, fast-start validation and SHA-256 hashing. Results are written to `reports/qa_results.json` and `reports/QA_REPORT.md`.

## Asset status

The source images are simulated construction and renovation visuals generated for this project. They are not records of real projects. Audio is synthesized by the renderer and contains no third-party recordings. See `ASSET_MANIFEST.md` for the full disclosure and licensing record.
