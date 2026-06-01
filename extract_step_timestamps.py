#!/usr/bin/env python3
import argparse
import csv
import datetime as dt
import math
import os
import statistics
from dataclasses import dataclass
from typing import List, Tuple


def moving_average(values: List[float], window: int) -> List[float]:
    if window <= 1 or not values:
        return values[:]

    out: List[float] = []
    running = 0.0
    queue: List[float] = []

    for v in values:
        queue.append(v)
        running += v
        if len(queue) > window:
            running -= queue.pop(0)
        out.append(running / len(queue))

    return out


def robust_threshold(values: List[float], floor: float = 0.35) -> float:
    if not values:
        return floor

    median = statistics.median(values)
    deviations = [abs(v - median) for v in values]
    mad = statistics.median(deviations)
    return median + max(floor, 2.5 * mad)


def load_accelerometer_samples(path: str) -> Tuple[List[int], List[float]]:
    timestamps: List[int] = []
    magnitudes: List[float] = []

    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("sensor") != "Accelerometer":
                continue
            ts = int(row["timestamp"])
            x = float(row["x"])
            y = float(row["y"])
            z = float(row["z"])
            magnitude = math.sqrt(x * x + y * y + z * z)
            timestamps.append(ts)
            magnitudes.append(magnitude)

    return timestamps, magnitudes


def detect_step_timestamps(
    timestamps_ms: List[int],
    magnitudes: List[float],
    gravity: float = 9.81,
    smooth_window: int = 5,
    min_interval_ms: int = 280,
) -> List[int]:
    if len(timestamps_ms) < 3:
        return []

    # Use deviation from gravity to isolate gait impacts independent of orientation.
    dynamic = [abs(m - gravity) for m in magnitudes]
    signal = moving_average(dynamic, smooth_window)
    threshold = robust_threshold(signal)

    step_indices: List[int] = []
    last_ts = -10**18

    for i in range(1, len(signal) - 1):
        center = signal[i]
        if center < threshold:
            continue
        if not (center > signal[i - 1] and center >= signal[i + 1]):
            continue

        left = min(signal[max(0, i - 3):i])
        right = min(signal[i + 1:min(len(signal), i + 4)])
        prominence = center - max(left, right)
        if prominence < 0.20:
            continue

        ts = timestamps_ms[i]
        if ts - last_ts < min_interval_ms:
            continue

        step_indices.append(i)
        last_ts = ts

    return [timestamps_ms[i] for i in step_indices]


def ms_to_iso8601(ts_ms: int) -> str:
    return dt.datetime.fromtimestamp(ts_ms / 1000.0, tz=dt.timezone.utc).isoformat()


@dataclass
class StepEvent:
    timestamp_ms: int
    sources: List[str]


def merge_step_streams(step_streams: List[Tuple[str, List[int]]], merge_gap_ms: int) -> List[StepEvent]:
    flat: List[Tuple[int, str]] = []
    for source, steps in step_streams:
        for ts in steps:
            flat.append((ts, source))

    if not flat:
        return []

    flat.sort(key=lambda item: item[0])
    merged: List[StepEvent] = []

    for ts, source in flat:
        if not merged:
            merged.append(StepEvent(timestamp_ms=ts, sources=[source]))
            continue

        prev = merged[-1]
        if ts - prev.timestamp_ms <= merge_gap_ms:
            if source not in prev.sources:
                prev.sources.append(source)
            continue

        merged.append(StepEvent(timestamp_ms=ts, sources=[source]))

    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract step timestamps from ankle tracker CSV")
    parser.add_argument("csv_paths", nargs="+", help="Path(s) to sensor CSV files")
    parser.add_argument("--min-interval-ms", type=int, default=280, help="Minimum time between steps")
    parser.add_argument("--smooth-window", type=int, default=5, help="Moving average window size")
    parser.add_argument("--gravity", type=float, default=9.81, help="Gravity magnitude")
    parser.add_argument(
        "--merge-gap-ms",
        type=int,
        default=120,
        help="Merge cross-leg detections that are very close in time",
    )
    parser.add_argument("--output", help="Optional output file path")
    args = parser.parse_args()

    per_file_steps: List[Tuple[str, List[int]]] = []
    for csv_path in args.csv_paths:
        timestamps, magnitudes = load_accelerometer_samples(csv_path)
        steps = detect_step_timestamps(
            timestamps,
            magnitudes,
            gravity=args.gravity,
            smooth_window=args.smooth_window,
            min_interval_ms=args.min_interval_ms,
        )
        per_file_steps.append((os.path.basename(csv_path), steps))

    merged_steps = merge_step_streams(per_file_steps, merge_gap_ms=args.merge_gap_ms)

    lines: List[str] = []
    lines.append(f"Detected steps (merged): {len(merged_steps)}")
    for source, steps in per_file_steps:
        lines.append(f"Detected in {source}: {len(steps)}")
    lines.append("timestamp_ms,timestamp_utc,sources")
    for event in merged_steps:
        source_text = ";".join(event.sources)
        lines.append(f"{event.timestamp_ms},{ms_to_iso8601(event.timestamp_ms)},{source_text}")

    output_text = "\n".join(lines)

    if args.output:
        with open(args.output, "w", newline="") as f:
            f.write(output_text)

    print(output_text)


if __name__ == "__main__":
    main()