#!/usr/bin/env python3
"""Render the construction portfolio samples with FFmpeg.

The visual source files are AI-generated concept images created for this
project. Audio is synthesized deterministically with NumPy, so the build does
not depend on third-party music or sound-effect files.
"""

from __future__ import annotations

import argparse
import math
import subprocess
import time
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUT = ROOT / "output"
REPORTS = ROOT / "reports"
FONT_DIR = Path("/usr/share/fonts/truetype/open-sans")
FPS = 30
WIDTH = 1080
HEIGHT = 1920
SAMPLE_RATE = 48_000


@dataclass(frozen=True)
class Clip:
    image: Path
    duration: float
    zoom_start: float
    zoom_end: float
    pan: str


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True)


def add_tone(
    track: np.ndarray,
    start: float,
    duration: float,
    frequency: float,
    amplitude: float,
    pan: float = 0.0,
    decay: float = 2.0,
) -> None:
    start_sample = max(0, int(start * SAMPLE_RATE))
    sample_count = min(int(duration * SAMPLE_RATE), len(track) - start_sample)
    if sample_count <= 0:
        return

    local_time = np.arange(sample_count, dtype=np.float64) / SAMPLE_RATE
    envelope = np.exp(-decay * local_time / max(duration, 0.001))
    wave_data = np.sin(2.0 * math.pi * frequency * local_time) * envelope * amplitude
    left_gain = math.sqrt((1.0 - pan) / 2.0)
    right_gain = math.sqrt((1.0 + pan) / 2.0)
    track[start_sample : start_sample + sample_count, 0] += wave_data * left_gain
    track[start_sample : start_sample + sample_count, 1] += wave_data * right_gain


def add_kick(track: np.ndarray, start: float, amplitude: float = 0.52) -> None:
    duration = 0.34
    start_sample = max(0, int(start * SAMPLE_RATE))
    sample_count = min(int(duration * SAMPLE_RATE), len(track) - start_sample)
    if sample_count <= 0:
        return

    local_time = np.arange(sample_count, dtype=np.float64) / SAMPLE_RATE
    phase = 2.0 * math.pi * (78.0 * local_time - 31.0 * local_time**2)
    envelope = np.exp(-12.0 * local_time)
    body = np.sin(phase) * envelope * amplitude
    click = np.sin(2.0 * math.pi * 1_900.0 * local_time) * np.exp(-85.0 * local_time) * 0.07
    track[start_sample : start_sample + sample_count, :] += (body + click)[:, None]


def add_noise_hit(
    track: np.ndarray,
    rng: np.random.Generator,
    start: float,
    duration: float,
    amplitude: float,
    pan: float = 0.0,
    rise: bool = False,
) -> None:
    start_sample = max(0, int(start * SAMPLE_RATE))
    sample_count = min(int(duration * SAMPLE_RATE), len(track) - start_sample)
    if sample_count <= 0:
        return

    noise = rng.normal(0.0, 1.0, sample_count)
    # A simple differentiator removes much of the low-frequency noise energy.
    noise = np.concatenate(([noise[0]], np.diff(noise)))
    progress = np.linspace(0.0, 1.0, sample_count, endpoint=False)
    envelope = progress**2 if rise else np.exp(-8.0 * progress)
    signal = noise * envelope * amplitude
    left_gain = math.sqrt((1.0 - pan) / 2.0)
    right_gain = math.sqrt((1.0 + pan) / 2.0)
    track[start_sample : start_sample + sample_count, 0] += signal * left_gain
    track[start_sample : start_sample + sample_count, 1] += signal * right_gain


def synthesize_progress_audio(path: Path, duration: float = 18.0) -> None:
    rng = np.random.default_rng(20261120)
    sample_count = int(duration * SAMPLE_RATE)
    track = np.zeros((sample_count, 2), dtype=np.float64)
    time_axis = np.arange(sample_count, dtype=np.float64) / SAMPLE_RATE

    # A restrained industrial pad gives the track musical continuity.
    chord_roots = (55.0, 65.41, 73.42, 82.41)
    section_length = duration / len(chord_roots)
    for index, root in enumerate(chord_roots):
        start = index * section_length
        end = min(duration, start + section_length + 0.2)
        mask = (time_axis >= start) & (time_axis < end)
        local_time = time_axis[mask] - start
        fade = np.minimum(1.0, local_time / 0.25) * np.minimum(1.0, (end - time_axis[mask]) / 0.35)
        pulse = 0.72 + 0.28 * np.sin(2.0 * math.pi * 0.5 * local_time)
        pad_left = (
            np.sin(2.0 * math.pi * root * local_time)
            + 0.44 * np.sin(2.0 * math.pi * root * 1.5 * local_time + 0.4)
            + 0.20 * np.sin(2.0 * math.pi * root * 2.0 * local_time + 0.8)
        )
        pad_right = (
            np.sin(2.0 * math.pi * root * local_time + 0.05)
            + 0.44 * np.sin(2.0 * math.pi * root * 1.5 * local_time + 0.52)
            + 0.20 * np.sin(2.0 * math.pi * root * 2.0 * local_time + 0.68)
        )
        track[mask, 0] += pad_left * fade * pulse * 0.055
        track[mask, 1] += pad_right * fade * pulse * 0.055

    beat_seconds = 60.0 / 106.0
    beat = 0.0
    beat_index = 0
    while beat < duration:
        add_kick(track, beat, 0.52 if beat_index % 4 == 0 else 0.35)
        if beat_index % 2 == 1:
            add_noise_hit(track, rng, beat, 0.10, 0.022, pan=0.35)
        add_tone(track, beat, 0.22, 110.0, 0.075, pan=-0.08, decay=4.5)
        half_beat = beat + beat_seconds / 2.0
        add_noise_hit(track, rng, half_beat, 0.07, 0.012, pan=-0.45)
        beat += beat_seconds
        beat_index += 1

    transition_times = (0.9, 4.9, 8.9, 12.9)
    for index, transition_time in enumerate(transition_times):
        add_noise_hit(
            track,
            rng,
            max(0.0, transition_time - 0.48),
            0.48,
            0.026,
            pan=-0.35 if index % 2 == 0 else 0.35,
            rise=True,
        )
        add_tone(track, transition_time, 0.55, 46.0, 0.36, decay=7.5)
        add_noise_hit(track, rng, transition_time, 0.28, 0.040, pan=0.0)

    # Short intro and final impacts frame the edit cleanly.
    add_tone(track, 0.0, 0.85, 39.0, 0.48, decay=5.0)
    add_tone(track, 17.25, 0.75, 55.0, 0.30, decay=3.5)

    fade_in = np.clip(time_axis / 0.08, 0.0, 1.0)
    fade_out = np.clip((duration - time_axis) / 0.55, 0.0, 1.0)
    track *= (fade_in * fade_out)[:, None]
    peak = float(np.max(np.abs(track)))
    if peak > 0.0:
        track *= 0.88 / peak

    pcm = np.round(track * 32767.0).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(pcm.tobytes())


def synthesize_safety_audio(path: Path, duration: float = 21.0) -> None:
    rng = np.random.default_rng(20261121)
    sample_count = int(duration * SAMPLE_RATE)
    track = np.zeros((sample_count, 2), dtype=np.float64)
    time_axis = np.arange(sample_count, dtype=np.float64) / SAMPLE_RATE

    # A low, stable pulse keeps this track controlled and corporate.
    roots = (65.41, 58.27, 55.0, 61.74, 65.41)
    section_length = duration / len(roots)
    for index, root in enumerate(roots):
        start = index * section_length
        end = min(duration, start + section_length + 0.12)
        mask = (time_axis >= start) & (time_axis < end)
        local_time = time_axis[mask] - start
        fade = np.minimum(1.0, local_time / 0.16) * np.minimum(1.0, (end - time_axis[mask]) / 0.22)
        gate = 0.62 + 0.38 * np.square(np.sin(2.0 * math.pi * 0.78 * local_time))
        left = (
            np.sin(2.0 * math.pi * root * local_time)
            + 0.32 * np.sin(2.0 * math.pi * root * 2.0 * local_time + 0.3)
        )
        right = (
            np.sin(2.0 * math.pi * root * local_time + 0.04)
            + 0.32 * np.sin(2.0 * math.pi * root * 2.0 * local_time + 0.42)
        )
        track[mask, 0] += left * fade * gate * 0.047
        track[mask, 1] += right * fade * gate * 0.047

    beat_seconds = 60.0 / 94.0
    beat = 0.0
    beat_index = 0
    while beat < duration:
        if beat_index % 4 in {0, 2}:
            add_kick(track, beat, 0.38 if beat_index % 4 == 0 else 0.26)
        add_tone(track, beat, 0.13, 146.83, 0.055, pan=-0.18, decay=7.0)
        add_noise_hit(track, rng, beat + beat_seconds / 2.0, 0.055, 0.010, pan=0.45)
        beat += beat_seconds
        beat_index += 1

    section_starts = (0.0, 4.13, 8.26, 12.39, 16.52)
    for index, section_start in enumerate(section_starts):
        add_tone(track, section_start, 0.24, 880.0, 0.105, pan=-0.22, decay=8.0)
        add_tone(track, section_start + 0.055, 0.22, 1_320.0, 0.075, pan=0.22, decay=9.0)
        if index > 0:
            add_noise_hit(
                track,
                rng,
                section_start - 0.24,
                0.24,
                0.014,
                pan=-0.3 if index % 2 else 0.3,
                rise=True,
            )
            add_tone(track, section_start, 0.42, 52.0, 0.27, decay=8.0)

    fade_in = np.clip(time_axis / 0.06, 0.0, 1.0)
    fade_out = np.clip((duration - time_axis) / 0.55, 0.0, 1.0)
    track *= (fade_in * fade_out)[:, None]
    peak = float(np.max(np.abs(track)))
    if peak > 0.0:
        track *= 0.88 / peak

    pcm = np.round(track * 32767.0).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(pcm.tobytes())


def synthesize_before_after_audio(path: Path, duration: float = 17.0) -> None:
    rng = np.random.default_rng(20261122)
    sample_count = int(duration * SAMPLE_RATE)
    track = np.zeros((sample_count, 2), dtype=np.float64)
    time_axis = np.arange(sample_count, dtype=np.float64) / SAMPLE_RATE

    roots = (55.0, 65.41, 73.42, 82.41)
    section_length = duration / len(roots)
    for index, root in enumerate(roots):
        start = index * section_length
        end = min(duration, start + section_length + 0.18)
        mask = (time_axis >= start) & (time_axis < end)
        local_time = time_axis[mask] - start
        fade = np.minimum(1.0, local_time / 0.18) * np.minimum(1.0, (end - time_axis[mask]) / 0.30)
        shimmer = 0.78 + 0.22 * np.sin(2.0 * math.pi * 0.36 * local_time)
        left = (
            np.sin(2.0 * math.pi * root * local_time)
            + 0.36 * np.sin(2.0 * math.pi * root * 2.0 * local_time + 0.22)
            + 0.13 * np.sin(2.0 * math.pi * root * 4.0 * local_time + 0.6)
        )
        right = (
            np.sin(2.0 * math.pi * root * local_time + 0.06)
            + 0.36 * np.sin(2.0 * math.pi * root * 2.0 * local_time + 0.38)
            + 0.13 * np.sin(2.0 * math.pi * root * 4.0 * local_time + 0.46)
        )
        track[mask, 0] += left * fade * shimmer * 0.050
        track[mask, 1] += right * fade * shimmer * 0.050

    beat_seconds = 60.0 / 122.0
    beat = 0.0
    beat_index = 0
    arpeggio = (220.0, 277.18, 329.63, 440.0)
    while beat < duration:
        add_kick(track, beat, 0.49 if beat_index % 4 == 0 else 0.31)
        note = arpeggio[beat_index % len(arpeggio)]
        add_tone(track, beat, 0.17, note, 0.055, pan=-0.35 if beat_index % 2 == 0 else 0.35, decay=7.0)
        add_noise_hit(track, rng, beat + beat_seconds / 2.0, 0.065, 0.014, pan=0.45)
        beat += beat_seconds
        beat_index += 1

    transition_times = (2.8, 5.8, 8.8, 12.0)
    for index, transition_time in enumerate(transition_times):
        add_noise_hit(
            track,
            rng,
            transition_time - 0.42,
            0.42,
            0.028,
            pan=-0.5 if index % 2 == 0 else 0.5,
            rise=True,
        )
        add_tone(track, transition_time, 0.50, 43.0, 0.38, decay=7.5)
        add_tone(track, transition_time + 0.04, 0.26, 659.25, 0.085, pan=0.2, decay=8.0)

    add_tone(track, 0.0, 0.75, 38.0, 0.50, decay=6.0)
    add_noise_hit(track, rng, 0.48, 2.05, 0.016, pan=0.0, rise=True)
    add_tone(track, 16.15, 0.75, 65.41, 0.31, decay=3.4)

    fade_in = np.clip(time_axis / 0.05, 0.0, 1.0)
    fade_out = np.clip((duration - time_axis) / 0.60, 0.0, 1.0)
    track *= (fade_in * fade_out)[:, None]
    peak = float(np.max(np.abs(track)))
    if peak > 0.0:
        track *= 0.88 / peak

    pcm = np.round(track * 32767.0).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(pcm.tobytes())


def ass_timestamp(seconds: float) -> str:
    centiseconds = int(round(seconds * 100.0))
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    whole_seconds, hundredths = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{whole_seconds:02d}.{hundredths:02d}"


def write_progress_subtitles(path: Path) -> None:
    events = [
        (0.0, 18.0, "Disclosure", "AI-GENERATED CONCEPT  •  DEMO"),
        (0.0, 18.0, "Header", "EDITING PORTFOLIO  /  CONSTRUCTION"),
        (0.0, 1.28, "Kicker", r"PROJECT SHOWCASE"),
        (0.0, 1.28, "Main", r"CONSTRUCTION\NIN MOTION"),
        (1.05, 4.82, "Kicker", r"PHASE 01  /  04"),
        (1.05, 4.82, "Main", r"GROUNDWORK"),
        (5.00, 8.82, "Kicker", r"PHASE 02  /  04"),
        (5.00, 8.82, "Main", r"STRUCTURE RISING"),
        (9.00, 12.82, "Kicker", r"PHASE 03  /  04"),
        (9.00, 12.82, "Main", r"ENCLOSURE COMPLETE"),
        (13.00, 17.28, "Kicker", r"PHASE 04  /  04"),
        (13.00, 17.28, "Main", r"BUILT TO DELIVER"),
        (17.28, 18.0, "Footnote", r"Simulated construction visuals for editing demonstration."),
    ]

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "WrapStyle: 0",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Disclosure,Open Sans Semibold,24,&H00FFFFFF,&H00FFFFFF,&H00000000,&H92000000,0,0,0,0,100,100,1,0,3,0,0,8,40,40,52,1",
        "Style: Header,Open Sans Semibold,25,&H00FFFFFF,&H00FFFFFF,&H60000000,&H00000000,0,0,0,0,100,100,2,0,1,1,0,7,70,70,156,1",
        "Style: Kicker,Open Sans Bold,27,&H0000B7FF,&H0000B7FF,&H70000000,&H00000000,-1,0,0,0,100,100,2,0,1,1,0,7,70,70,1330,1",
        "Style: Main,Open Sans ExtraBold,68,&H00FFFFFF,&H00FFFFFF,&H80000000,&H00000000,-1,0,0,0,100,100,-1,0,1,2,0,7,70,60,1375,1",
        "Style: Footnote,Open Sans Semibold,25,&H00FFFFFF,&H00FFFFFF,&H00000000,&H98000000,0,0,0,0,100,100,0,0,3,0,0,2,70,70,260,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for start, end, style, text in events:
        fade = r"{\fad(160,180)}" if style not in {"Disclosure", "Header"} else ""
        lines.append(
            f"Dialogue: 0,{ass_timestamp(start)},{ass_timestamp(end)},{style},,0,0,0,,{fade}{text}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_safety_subtitles(path: Path) -> None:
    events = [
        (0.0, 21.0, "Disclosure", "AI-GENERATED CONCEPT  •  DEMO"),
        (0.0, 21.0, "Header", "SITE SAFETY  /  FIELD SYSTEM"),
        (0.10, 3.98, "Kicker", "CONTROL 01  /  05"),
        (0.10, 3.98, "Main", "PPE CHECKED"),
        (4.25, 8.11, "Kicker", "CONTROL 02  /  05"),
        (4.25, 8.11, "Main", "ACCESS ROUTES CLEAR"),
        (8.38, 12.24, "Kicker", "CONTROL 03  /  05"),
        (8.38, 12.24, "Main", "LIFT PLAN CONFIRMED"),
        (12.51, 16.37, "Kicker", "CONTROL 04  /  05"),
        (12.51, 16.37, "Main", "TEAM COMMUNICATION"),
        (16.64, 20.25, "Kicker", "CONTROL 05  /  05"),
        (16.64, 20.25, "Main", "TOOLS INSPECTED"),
        (20.25, 21.0, "Final", "SAFE START.  STRONG FINISH."),
        (20.25, 21.0, "Footnote", "Simulated site visuals for editing demonstration."),
    ]

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "WrapStyle: 0",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Disclosure,Open Sans Semibold,24,&H00FFFFFF,&H00FFFFFF,&H00000000,&H9206172C,0,0,0,0,100,100,1,0,3,0,0,8,40,40,52,1",
        "Style: Header,Open Sans Semibold,25,&H00FFFFFF,&H00FFFFFF,&H7006172C,&H00000000,0,0,0,0,100,100,2,0,1,1,0,7,70,70,156,1",
        "Style: Kicker,Open Sans Bold,27,&H0000D7FF,&H0000D7FF,&H8006172C,&H00000000,-1,0,0,0,100,100,2,0,1,1,0,7,72,70,1325,1",
        "Style: Main,Open Sans ExtraBold,62,&H00FFFFFF,&H00FFFFFF,&H9006172C,&H00000000,-1,0,0,0,100,100,-1,0,1,2,0,7,72,55,1375,1",
        "Style: Final,Open Sans ExtraBold,52,&H0000D7FF,&H0000D7FF,&H9006172C,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,7,72,55,1372,1",
        "Style: Footnote,Open Sans Semibold,24,&H00FFFFFF,&H00FFFFFF,&H00000000,&H9A06172C,0,0,0,0,100,100,0,0,3,0,0,2,60,60,255,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for start, end, style, text in events:
        fade = r"{\fad(130,150)}" if style not in {"Disclosure", "Header"} else ""
        lines.append(
            f"Dialogue: 0,{ass_timestamp(start)},{ass_timestamp(end)},{style},,0,0,0,,{fade}{text}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_before_after_subtitles(path: Path) -> None:
    events = [
        (0.0, 17.0, "Disclosure", "AI-GENERATED CONCEPT  •  DEMO"),
        (0.0, 17.0, "Header", "TRANSFORMATION STUDY  /  INTERIOR"),
        (0.0, 2.72, "BeforeLabel", "BEFORE"),
        (0.0, 2.72, "AfterLabel", "AFTER"),
        (0.0, 2.72, "Main", "THE TRANSFORMATION"),
        (2.95, 5.65, "Kicker", "01  /  EXISTING"),
        (2.95, 5.65, "Main", "RAW SHELL"),
        (5.95, 8.65, "Kicker", "02  /  COMPLETE"),
        (5.95, 8.65, "Main", "FINISHED SPACE"),
        (8.95, 11.85, "Kicker", "DETAIL STUDY"),
        (8.95, 11.85, "Main", "DETAILS REFINED"),
        (12.15, 16.25, "Kicker", "FINAL REVEAL"),
        (12.15, 16.25, "Main", "READY FOR HANDOVER"),
        (16.25, 17.0, "Footnote", "Simulated renovation visuals for editing demonstration."),
    ]

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "WrapStyle: 0",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Disclosure,Open Sans Semibold,24,&H00FFFFFF,&H00FFFFFF,&H00000000,&H92000000,0,0,0,0,100,100,1,0,3,0,0,8,40,40,52,1",
        "Style: Header,Open Sans Semibold,25,&H00FFFFFF,&H00FFFFFF,&H70000000,&H00000000,0,0,0,0,100,100,2,0,1,1,0,7,70,70,156,1",
        "Style: BeforeLabel,Open Sans ExtraBold,27,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB0000000,-1,0,0,0,100,100,2,0,3,0,0,7,70,70,280,1",
        "Style: AfterLabel,Open Sans ExtraBold,27,&H0000CBFF,&H0000CBFF,&H00000000,&HB0000000,-1,0,0,0,100,100,2,0,3,0,0,9,70,70,280,1",
        "Style: Kicker,Open Sans Bold,27,&H0000CBFF,&H0000CBFF,&H80000000,&H00000000,-1,0,0,0,100,100,2,0,1,1,0,7,70,70,1340,1",
        "Style: Main,Open Sans ExtraBold,64,&H00FFFFFF,&H00FFFFFF,&H90000000,&H00000000,-1,0,0,0,100,100,-1,0,1,2,0,7,70,55,1390,1",
        "Style: Footnote,Open Sans Semibold,24,&H00FFFFFF,&H00FFFFFF,&H00000000,&H9A000000,0,0,0,0,100,100,0,0,3,0,0,2,60,60,250,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for start, end, style, text in events:
        fade = r"{\fad(130,160)}" if style not in {"Disclosure", "Header"} else ""
        lines.append(
            f"Dialogue: 0,{ass_timestamp(start)},{ass_timestamp(end)},{style},,0,0,0,,{fade}{text}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def zoompan_filter(clip: Clip, index: int) -> str:
    frame_count = max(2, int(round(clip.duration * FPS)))
    progress = f"on/{frame_count - 1}"
    zoom = f"{clip.zoom_start:.5f}+({clip.zoom_end - clip.zoom_start:.5f})*pow({progress},1.18)"
    centered_x = "iw/2-(iw/zoom/2)"
    centered_y = "ih/2-(ih/zoom/2)"
    if clip.pan == "right":
        x_expr = f"(iw-iw/zoom)*(0.08+0.84*{progress})"
        y_expr = centered_y
    elif clip.pan == "left":
        x_expr = f"(iw-iw/zoom)*(0.92-0.84*{progress})"
        y_expr = centered_y
    elif clip.pan == "up":
        x_expr = centered_x
        y_expr = f"(ih-ih/zoom)*(0.86-0.68*{progress})"
    elif clip.pan == "down":
        x_expr = centered_x
        y_expr = f"(ih-ih/zoom)*(0.16+0.68*{progress})"
    else:
        x_expr = centered_x
        y_expr = centered_y

    return (
        f"[{index}:v]scale=1200:2134:force_original_aspect_ratio=increase,"
        f"crop=1200:2134,"
        f"zoompan=z='{zoom}':x='{x_expr}':y='{y_expr}':d=1:s={WIDTH}x{HEIGHT}:fps={FPS},"
        f"trim=duration={clip.duration:.3f},setpts=PTS-STARTPTS,"
        f"fps={FPS},setsar=1[v{index}]"
    )


def render_progress() -> tuple[Path, float]:
    duration = 18.0
    clips = [
        Clip(ASSETS / "progress/04_complete.png", 1.4, 1.11, 1.03, "center"),
        Clip(ASSETS / "progress/01_foundation.png", 4.5, 1.03, 1.11, "right"),
        Clip(ASSETS / "progress/02_structure.png", 4.5, 1.11, 1.07, "up"),
        Clip(ASSETS / "progress/03_enclosure.png", 4.5, 1.08, 1.13, "left"),
        Clip(ASSETS / "progress/04_complete.png", 5.1, 1.10, 1.025, "center"),
    ]
    for clip in clips:
        if not clip.image.is_file():
            raise FileNotFoundError(f"Missing visual asset: {clip.image}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    audio_path = OUTPUT / "progress_audio.wav"
    subtitle_path = OUTPUT / "progress.ass"
    video_path = OUTPUT / "01_construction_progress.mp4"
    synthesize_progress_audio(audio_path, duration)
    write_progress_subtitles(subtitle_path)

    command = ["ffmpeg", "-y", "-hide_banner"]
    for clip in clips:
        command.extend(
            ["-loop", "1", "-framerate", str(FPS), "-t", f"{clip.duration:.3f}", "-i", str(clip.image)]
        )
    command.extend(["-i", str(audio_path)])

    filters = [zoompan_filter(clip, index) for index, clip in enumerate(clips)]
    filters.extend(
        [
            "[v0][v1]xfade=transition=smoothleft:duration=0.5:offset=0.9,fps=30[x1]",
            "[x1][v2]xfade=transition=wipeup:duration=0.5:offset=4.9,fps=30[x2]",
            "[x2][v3]xfade=transition=smoothup:duration=0.5:offset=8.9,fps=30[x3]",
            "[x3][v4]xfade=transition=fade:duration=0.5:offset=12.9,fps=30[x4]",
        ]
    )

    base_overlay = (
        "[x4]trim=duration=18,setpts=PTS-STARTPTS,"
        "eq=contrast=1.035:saturation=0.96:brightness=-0.008,"
        "vignette=PI/5:eval=frame,"
        "noise=alls=1.8:allf=t,"
        "drawbox=x=54:y=1290:w=972:h=294:color=black@0.30:t=fill,"
        "drawbox=x=70:y=1560:w=940:h=6:color=white@0.30:t=fill"
    )
    stage_starts = (1.05, 5.0, 9.0, 13.0)
    stage_x = (70, 310, 550, 790)
    for start, x_pos in zip(stage_starts, stage_x, strict=True):
        base_overlay += (
            f",drawbox=x={x_pos}:y=1560:w=220:h=6:color=0xFFB400@1.0:t=fill:enable='gte(t,{start})'"
        )
    subtitle_filter = str(subtitle_path).replace("'", r"\'")
    font_filter = str(FONT_DIR).replace("'", r"\'")
    base_overlay += (
        f",subtitles=filename='{subtitle_filter}':fontsdir='{font_filter}',"
        "format=yuv420p[outv]"
    )
    filters.append(base_overlay)

    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[outv]",
            "-map",
            "5:a:0",
            "-af",
            "highpass=f=28,lowpass=f=16000,acompressor=threshold=-18dB:ratio=2.2:attack=12:release=120,alimiter=limit=0.89,loudnorm=I=-15:TP=-1.5:LRA=7",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-profile:v",
            "high",
            "-level",
            "4.1",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "2",
            "-t",
            f"{duration:.3f}",
            "-movflags",
            "+faststart",
            str(video_path),
        ]
    )

    started = time.perf_counter()
    run(command)
    elapsed = time.perf_counter() - started
    (REPORTS / "01_render_time.txt").write_text(f"{elapsed:.3f} seconds\n", encoding="utf-8")
    return video_path, elapsed


def render_safety() -> tuple[Path, float]:
    duration = 21.0
    clip_duration = 4.48
    clips = [
        Clip(ASSETS / "safety/01_ppe.png", clip_duration, 1.035, 1.085, "right"),
        Clip(ASSETS / "safety/02_access_route.png", clip_duration, 1.075, 1.115, "up"),
        Clip(ASSETS / "safety/03_lift_plan.png", clip_duration, 1.055, 1.095, "left"),
        Clip(ASSETS / "safety/04_communication.png", clip_duration, 1.095, 1.045, "center"),
        Clip(ASSETS / "safety/05_tools.png", clip_duration, 1.045, 1.10, "down"),
    ]
    for clip in clips:
        if not clip.image.is_file():
            raise FileNotFoundError(f"Missing visual asset: {clip.image}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    audio_path = OUTPUT / "safety_audio.wav"
    subtitle_path = OUTPUT / "safety.ass"
    video_path = OUTPUT / "02_construction_safety.mp4"
    synthesize_safety_audio(audio_path, duration)
    write_safety_subtitles(subtitle_path)

    command = ["ffmpeg", "-y", "-hide_banner"]
    for clip in clips:
        command.extend(
            ["-loop", "1", "-framerate", str(FPS), "-t", f"{clip.duration:.3f}", "-i", str(clip.image)]
        )
    command.extend(["-i", str(audio_path)])

    filters = [zoompan_filter(clip, index) for index, clip in enumerate(clips)]
    filters.extend(
        [
            "[v0][v1]xfade=transition=coverleft:duration=0.35:offset=4.13,fps=30[x1]",
            "[x1][v2]xfade=transition=smoothleft:duration=0.35:offset=8.26,fps=30[x2]",
            "[x2][v3]xfade=transition=revealup:duration=0.35:offset=12.39,fps=30[x3]",
            "[x3][v4]xfade=transition=coverdown:duration=0.35:offset=16.52,fps=30[x4]",
        ]
    )

    base_overlay = (
        "[x4]trim=duration=21,setpts=PTS-STARTPTS,"
        "eq=contrast=1.055:saturation=0.91:brightness=-0.012,"
        "colorbalance=bs=.025:gs=.008,"
        "vignette=PI/5.5:eval=frame,"
        "noise=alls=1.6:allf=t,"
        "drawbox=x=44:y=1260:w=992:h=314:color=0x06172C@0.66:t=fill,"
        "drawbox=x=44:y=1260:w=992:h=314:color=0x76A4C6@0.32:t=2"
    )
    stage_starts = (0.0, 4.13, 8.26, 12.39, 16.52)
    stage_ends = (4.13, 8.26, 12.39, 16.52, 21.0)
    stage_x = (70, 258, 446, 634, 822)
    for x_pos in stage_x:
        base_overlay += f",drawbox=x={x_pos}:y=1548:w=168:h=7:color=white@0.25:t=fill"
    for start, end, x_pos in zip(stage_starts, stage_ends, stage_x, strict=True):
        base_overlay += (
            f",drawbox=x={x_pos}:y=1548:w=168:h=7:color=0xFFD700@1.0:t=fill:"
            f"enable='between(t,{start},{end})'"
        )
    subtitle_filter = str(subtitle_path).replace("'", r"\'")
    font_filter = str(FONT_DIR).replace("'", r"\'")
    base_overlay += (
        f",subtitles=filename='{subtitle_filter}':fontsdir='{font_filter}',"
        "format=yuv420p[outv]"
    )
    filters.append(base_overlay)

    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[outv]",
            "-map",
            "5:a:0",
            "-af",
            "highpass=f=30,lowpass=f=15500,acompressor=threshold=-19dB:ratio=2.0:attack=10:release=110,alimiter=limit=0.89,loudnorm=I=-15:TP=-1.5:LRA=7",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-profile:v",
            "high",
            "-level",
            "4.1",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "2",
            "-t",
            f"{duration:.3f}",
            "-movflags",
            "+faststart",
            str(video_path),
        ]
    )

    started = time.perf_counter()
    run(command)
    elapsed = time.perf_counter() - started
    (REPORTS / "02_render_time.txt").write_text(f"{elapsed:.3f} seconds\n", encoding="utf-8")
    return video_path, elapsed


def render_before_after() -> tuple[Path, float]:
    duration = 17.0
    clips = [
        Clip(ASSETS / "before_after/01_office_before.png", 3.0, 1.035, 1.075, "center"),
        Clip(ASSETS / "before_after/01_office_after.png", 3.0, 1.035, 1.075, "center"),
        Clip(ASSETS / "before_after/01_office_before.png", 3.2, 1.045, 1.10, "right"),
        Clip(ASSETS / "before_after/01_office_after.png", 3.2, 1.095, 1.035, "left"),
        Clip(ASSETS / "before_after/02_lobby_before.png", 3.4, 1.04, 1.085, "center"),
        Clip(ASSETS / "before_after/02_lobby_after.png", 3.4, 1.04, 1.085, "center"),
        Clip(ASSETS / "before_after/02_lobby_after.png", 5.0, 1.10, 1.025, "center"),
    ]
    for clip in clips:
        if not clip.image.is_file():
            raise FileNotFoundError(f"Missing visual asset: {clip.image}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    audio_path = OUTPUT / "before_after_audio.wav"
    subtitle_path = OUTPUT / "before_after.ass"
    video_path = OUTPUT / "03_before_after_transformation.mp4"
    synthesize_before_after_audio(audio_path, duration)
    write_before_after_subtitles(subtitle_path)

    command = ["ffmpeg", "-y", "-hide_banner"]
    for clip in clips:
        command.extend(
            ["-loop", "1", "-framerate", str(FPS), "-t", f"{clip.duration:.3f}", "-i", str(clip.image)]
        )
    command.extend(["-i", str(audio_path)])

    filters = [zoompan_filter(clip, index) for index, clip in enumerate(clips)]
    split_one_blend = (
        "if(lte(X,W*if(lt(T,0.45),0.5,"
        "if(lt(T,0.85),0.5+0.28*(T-0.45)/0.40,"
        "if(lt(T,2.60),0.78-0.60*(T-0.85)/1.75,0.18)))),A,B)"
    )
    split_one_overlay = (
        "if(lt(t,0.45),0.5,"
        "if(lt(t,0.85),0.5+0.28*(t-0.45)/0.40,"
        "if(lt(t,2.60),0.78-0.60*(t-0.85)/1.75,0.18)))"
    )
    split_two_blend = "if(lte(X,W*max(0.16,0.82-0.66*T/2.85)),A,B)"
    split_two_overlay = "max(0.16,0.82-0.66*t/2.85)"
    filters.extend(
        [
            "[v0]eq=saturation=0.68:contrast=1.055:brightness=-0.018,colorbalance=bs=.045[before1]",
            "[v1]eq=saturation=1.05:contrast=1.025:brightness=0.008,colorbalance=rs=.028[after1]",
            f"[before1][after1]blend=all_expr='{split_one_blend}'[reveal1base]",
            "color=c=white@0.96:s=6x1920:r=30:d=3.0[line1]",
            f"[reveal1base][line1]overlay=x='main_w*({split_one_overlay})-3':y=0:eval=frame:shortest=1,fps=30[reveal1]",
            "[v2]eq=saturation=0.66:contrast=1.06:brightness=-0.02,colorbalance=bs=.05[before_full]",
            "[v3]eq=saturation=1.05:contrast=1.02:brightness=.008,colorbalance=rs=.03[after_full]",
            "[v4]eq=saturation=0.66:contrast=1.06:brightness=-0.02,colorbalance=bs=.05[before2]",
            "[v5]eq=saturation=1.06:contrast=1.02:brightness=.01,colorbalance=rs=.035[after2]",
            f"[before2][after2]blend=all_expr='{split_two_blend}'[reveal2base]",
            "color=c=white@0.96:s=6x1920:r=30:d=3.4[line2]",
            f"[reveal2base][line2]overlay=x='main_w*({split_two_overlay})-3':y=0:eval=frame:shortest=1,fps=30[reveal2]",
            "[v6]eq=saturation=1.06:contrast=1.02:brightness=.01,colorbalance=rs=.035[after_hero]",
            "[reveal1][before_full]xfade=transition=fadefast:duration=0.2:offset=2.8,fps=30[x1]",
            "[x1][after_full]xfade=transition=wiperight:duration=0.2:offset=5.8,fps=30[x2]",
            "[x2][reveal2]xfade=transition=diagtl:duration=0.2:offset=8.8,fps=30[x3]",
            "[x3][after_hero]xfade=transition=smoothright:duration=0.2:offset=12.0,fps=30[x4]",
        ]
    )

    subtitle_filter = str(subtitle_path).replace("'", r"\'")
    font_filter = str(FONT_DIR).replace("'", r"\'")
    filters.append(
        "[x4]trim=duration=17,setpts=PTS-STARTPTS,"
        "vignette=PI/5.8:eval=frame,noise=alls=1.45:allf=t,"
        "drawbox=x=48:y=1300:w=984:h=255:color=black@0.38:t=fill,"
        "drawbox=x=70:y=1565:w=940:h=4:color=white@0.72:t=fill,"
        f"subtitles=filename='{subtitle_filter}':fontsdir='{font_filter}',"
        "format=yuv420p[outv]"
    )

    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[outv]",
            "-map",
            "7:a:0",
            "-af",
            "highpass=f=28,lowpass=f=16500,acompressor=threshold=-18dB:ratio=2.1:attack=10:release=115,alimiter=limit=0.89,loudnorm=I=-15:TP=-1.5:LRA=7",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-profile:v",
            "high",
            "-level",
            "4.1",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "2",
            "-t",
            f"{duration:.3f}",
            "-movflags",
            "+faststart",
            str(video_path),
        ]
    )

    started = time.perf_counter()
    run(command)
    elapsed = time.perf_counter() - started
    (REPORTS / "03_render_time.txt").write_text(f"{elapsed:.3f} seconds\n", encoding="utf-8")
    return video_path, elapsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sample",
        choices=("all", "progress", "safety", "before-after"),
        default="all",
        help="Sample to render",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.sample == "all":
        for renderer in (render_progress, render_safety, render_before_after):
            path, elapsed = renderer()
            print(f"Rendered {path} in {elapsed:.2f} seconds")
        return
    if args.sample == "progress":
        path, elapsed = render_progress()
    elif args.sample == "safety":
        path, elapsed = render_safety()
    elif args.sample == "before-after":
        path, elapsed = render_before_after()
    else:
        raise ValueError(f"Unsupported sample: {args.sample}")
    print(f"Rendered {path} in {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
