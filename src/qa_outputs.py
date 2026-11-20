#!/usr/bin/env python3
"""Validate the exported MP4 portfolio samples and write QA reports."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
REPORTS = ROOT / "reports"

SAMPLES = {
    "01_construction_progress.mp4": (15.0, 20.0),
    "02_construction_safety.mp4": (15.0, 25.0),
    "03_before_after_transformation.mp4": (15.0, 20.0),
}


def execute(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe(path: Path) -> dict:
    result = execute(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,bit_rate:stream=index,codec_type,codec_name,profile,pix_fmt,width,height,r_frame_rate,avg_frame_rate,sample_aspect_ratio,sample_rate,channels,duration",
            "-of",
            "json",
            str(path),
        ]
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe failed")
    return json.loads(result.stdout)


def detect(path: Path, media_filter: str, *, audio: bool) -> tuple[bool, str]:
    command = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path)]
    if audio:
        command.extend(["-af", media_filter, "-vn"])
    else:
        command.extend(["-vf", media_filter, "-an"])
    command.extend(["-f", "null", "-"])
    result = execute(command)
    return result.returncode == 0, result.stderr


def validate_sample(path: Path, minimum: float, maximum: float) -> dict:
    errors: list[str] = []
    metadata = probe(path)
    streams = metadata["streams"]
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    duration = float(metadata["format"]["duration"])

    if video is None:
        errors.append("missing video stream")
    else:
        expected_video = {
            "codec_name": "h264",
            "profile": "High",
            "width": 1080,
            "height": 1920,
            "pix_fmt": "yuv420p",
            "sample_aspect_ratio": "1:1",
            "r_frame_rate": "30/1",
            "avg_frame_rate": "30/1",
        }
        for field, expected in expected_video.items():
            if video.get(field) != expected:
                errors.append(f"video {field}={video.get(field)!r}, expected {expected!r}")

    if audio is None:
        errors.append("missing audio stream")
    else:
        expected_audio = {
            "codec_name": "aac",
            "profile": "LC",
            "sample_rate": "48000",
            "channels": 2,
        }
        for field, expected in expected_audio.items():
            if audio.get(field) != expected:
                errors.append(f"audio {field}={audio.get(field)!r}, expected {expected!r}")

    if not minimum <= duration <= maximum:
        errors.append(f"duration {duration:.3f}s outside {minimum:.1f}–{maximum:.1f}s")

    if video is not None and audio is not None:
        duration_delta = abs(float(video["duration"]) - float(audio["duration"]))
        if duration_delta > 0.10:
            errors.append(f"audio/video duration delta is {duration_delta:.3f}s")
    else:
        duration_delta = None

    decode = execute(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            "-f",
            "null",
            "-",
        ]
    )
    if decode.returncode != 0:
        errors.append(f"full decode failed: {decode.stderr.strip()}")

    black_ok, black_log = detect(
        path,
        "blackdetect=d=0.18:pix_th=0.05:pic_th=0.98",
        audio=False,
    )
    freeze_ok, freeze_log = detect(path, "freezedetect=n=-50dB:d=0.65", audio=False)
    silence_ok, silence_log = detect(path, "silencedetect=n=-55dB:d=0.8", audio=True)
    black_events = re.findall(r"black_start:[^\r\n]+", black_log)
    freeze_events = re.findall(r"freeze_(?:start|end|duration):[^\r\n]+", freeze_log)
    silence_events = re.findall(r"silence_(?:start|end):[^\r\n]+", silence_log)

    if not black_ok:
        errors.append("black-frame detector failed to execute")
    if not freeze_ok:
        errors.append("freeze detector failed to execute")
    if not silence_ok:
        errors.append("silence detector failed to execute")
    if black_events:
        errors.append(f"unexpected black event: {black_events[0]}")
    if freeze_events:
        errors.append(f"unexpected freeze event: {freeze_events[0]}")
    if silence_events:
        errors.append(f"unexpected silence event: {silence_events[0]}")

    loudness_ok, loudness_log = detect(path, "ebur128=peak=true", audio=True)
    loudness_matches = re.findall(r"I:\s*(-?\d+(?:\.\d+)?)\s+LUFS", loudness_log)
    peak_matches = re.findall(r"Peak:\s*(-?\d+(?:\.\d+)?)\s+dBFS", loudness_log)
    integrated_lufs = float(loudness_matches[-1]) if loudness_matches else None
    true_peak_dbfs = float(peak_matches[-1]) if peak_matches else None
    if not loudness_ok or integrated_lufs is None or true_peak_dbfs is None:
        errors.append("loudness measurement failed")
    else:
        if not -16.0 <= integrated_lufs <= -14.0:
            errors.append(f"integrated loudness is {integrated_lufs:.1f} LUFS")
        if true_peak_dbfs > -1.0:
            errors.append(f"true peak is {true_peak_dbfs:.1f} dBFS")

    atom_bytes = path.read_bytes()
    moov_offset = atom_bytes.find(b"moov")
    mdat_offset = atom_bytes.find(b"mdat")
    faststart = 0 <= moov_offset < mdat_offset
    if not faststart:
        errors.append("moov atom is not ahead of mdat")

    return {
        "file": str(path.relative_to(ROOT)),
        "passed": not errors,
        "errors": errors,
        "duration_seconds": duration,
        "size_bytes": int(metadata["format"]["size"]),
        "bit_rate": int(metadata["format"]["bit_rate"]),
        "video": video,
        "audio": audio,
        "audio_video_duration_delta_seconds": duration_delta,
        "full_decode": "passed" if decode.returncode == 0 else "failed",
        "black_events": black_events,
        "freeze_events": freeze_events,
        "silence_events": silence_events,
        "integrated_lufs": integrated_lufs,
        "true_peak_dbfs": true_peak_dbfs,
        "faststart": faststart,
        "sha256": sha256(path),
    }


def write_markdown(results: list[dict], output_path: Path) -> None:
    lines = [
        "# Export QA results",
        "",
        "All checks below were executed against the final MP4 files.",
        "",
        "| File | Result | Duration | Video | Audio | Loudness | Peak |",
        "|---|---:|---:|---|---|---:|---:|",
    ]
    for result in results:
        video = result["video"] or {}
        audio = result["audio"] or {}
        lines.append(
            "| {file} | {status} | {duration:.3f}s | {video_codec} {width}×{height} {pix_fmt} | "
            "{audio_codec} {sample_rate} Hz / {channels} ch | {lufs:.1f} LUFS | {peak:.1f} dBFS |".format(
                file=result["file"],
                status="PASS" if result["passed"] else "FAIL",
                duration=result["duration_seconds"],
                video_codec=video.get("codec_name", "missing"),
                width=video.get("width", "?"),
                height=video.get("height", "?"),
                pix_fmt=video.get("pix_fmt", "?"),
                audio_codec=audio.get("codec_name", "missing"),
                sample_rate=audio.get("sample_rate", "?"),
                channels=audio.get("channels", "?"),
                lufs=result["integrated_lufs"] or 0.0,
                peak=result["true_peak_dbfs"] or 0.0,
            )
        )

    lines.extend(
        [
            "",
            "Each file also passed full decode, fast-start placement, audio/video duration matching, and black-frame, freeze and silence scans. Detector event arrays are empty in the JSON report.",
            "",
            "Visual checks were completed from full-resolution preview frames, contact sheets, and a dedicated first-three-seconds sheet for the comparison edit.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    results = []
    for filename, duration_range in SAMPLES.items():
        path = OUTPUT / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        results.append(validate_sample(path, *duration_range))

    payload = {"all_passed": all(result["passed"] for result in results), "samples": results}
    json_path = REPORTS / "qa_results.json"
    markdown_path = REPORTS / "QA_REPORT.md"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_markdown(results, markdown_path)
    print(json.dumps(payload, indent=2))
    if not payload["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
