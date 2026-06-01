#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path
from statistics import mean

import matplotlib.pyplot as plt


def moving_average(values: list[float], window: int) -> list[float]:
    if window <= 1 or not values:
        return values[:]
    out: list[float] = []
    running = 0.0
    queue: list[float] = []
    for value in values:
        queue.append(value)
        running += value
        if len(queue) > window:
            running -= queue.pop(0)
        out.append(running / len(queue))
    return out


def parse_step_timestamps(file_path: Path) -> list[int]:
    timestamps: list[int] = []
    with file_path.open("r", newline="") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("Detected") or line.startswith("timestamp_ms"):
                continue
            first_col = line.split(",", 1)[0]
            try:
                timestamps.append(int(first_col))
            except ValueError:
                continue
    timestamps.sort()
    return timestamps


def compute_step_speed_spm(timestamps_ms: list[int]) -> tuple[list[float], list[float]]:
    if len(timestamps_ms) < 2:
        return [], []

    times_s: list[float] = []
    speed_spm: list[float] = []
    start = timestamps_ms[0]

    for previous, current in zip(timestamps_ms[:-1], timestamps_ms[1:]):
        delta_ms = current - previous
        if delta_ms <= 0:
            continue
        times_s.append((current - start) / 1000.0)
        speed_spm.append(60000.0 / delta_ms)

    return times_s, speed_spm


def save_summary_csv(rows: list[dict[str, str]], path: Path) -> None:
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["file", "step_count", "avg_spm", "min_spm", "max_spm"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate step-speed chart from results files")
    parser.add_argument("--results-dir", default="results", help="Directory containing step timestamp txt files")
    parser.add_argument("--output", default="results/step_speed_chart.png", help="Output chart path")
    parser.add_argument("--summary", default="results/step_speed_summary.csv", help="Output summary CSV path")
    parser.add_argument("--smooth-window", type=int, default=5, help="Smoothing window for speed series")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    files = sorted(results_dir.glob("step_timestamps*.txt"))
    if not files:
        raise SystemExit(f"No matching files found in {results_dir}")

    chart_data: list[tuple[str, list[float], list[float], list[float]]] = []
    summary_rows: list[dict[str, str]] = []

    for file_path in files:
        timestamps = parse_step_timestamps(file_path)
        times_s, speed_spm = compute_step_speed_spm(timestamps)
        smoothed = moving_average(speed_spm, max(1, args.smooth_window))

        if speed_spm:
            summary_rows.append(
                {
                    "file": file_path.name,
                    "step_count": str(len(timestamps)),
                    "avg_spm": f"{mean(speed_spm):.2f}",
                    "min_spm": f"{min(speed_spm):.2f}",
                    "max_spm": f"{max(speed_spm):.2f}",
                }
            )
        else:
            summary_rows.append(
                {
                    "file": file_path.name,
                    "step_count": str(len(timestamps)),
                    "avg_spm": "",
                    "min_spm": "",
                    "max_spm": "",
                }
            )

        chart_data.append((file_path.name, times_s, speed_spm, smoothed))

    fig, axes = plt.subplots(len(chart_data), 1, figsize=(12, max(4, len(chart_data) * 3.2)), sharex=False)
    if len(chart_data) == 1:
        axes = [axes]

    for ax, (name, times_s, speed_spm, smoothed) in zip(axes, chart_data):
        if not times_s:
            ax.text(0.5, 0.5, "Not enough data", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(name)
            ax.set_ylabel("SPM")
            continue

        ax.plot(times_s, speed_spm, color="#8aa5c2", alpha=0.35, linewidth=1, label="Instant")
        ax.plot(times_s, smoothed, color="#1f4e79", linewidth=2, label="Smoothed")
        ax.set_title(name)
        ax.set_ylabel("Step Speed (SPM)")
        ax.grid(alpha=0.2)
        ax.legend(loc="upper right")

    axes[-1].set_xlabel("Time Since First Step (seconds)")
    fig.suptitle("Step Speed Over Time", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.97])

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)

    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    save_summary_csv(summary_rows, summary_path)

    print(f"Chart saved to: {output_path}")
    print(f"Summary saved to: {summary_path}")


if __name__ == "__main__":
    main()