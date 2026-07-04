from pathlib import Path
import csv
import datetime as dt
import matplotlib.pyplot as plt

CSV_PATH = Path(__file__).resolve().parent.parent / "data-2" / "sensor_data_20260607_215226.csv"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "results" / "accelerator_axes_20260607_215226.png"

COLORS = {
    "x": "#1f4e79",
    "y": "#b22222",
    "z": "#d4a373",
}

SMOOTH_WINDOW = 5


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


def load_accelerometer_axes(path: Path) -> tuple[list[int], list[float], list[float], list[float]]:
    timestamps: list[int] = []
    x_values: list[float] = []
    y_values: list[float] = []
    z_values: list[float] = []

    with path.open("r", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row.get("sensor") != "Accelerometer":
                continue
            timestamps.append(int(row["timestamp"]))
            x_values.append(float(row["x"]))
            y_values.append(float(row["y"]))
            z_values.append(float(row["z"]))

    return timestamps, x_values, y_values, z_values


if __name__ == "__main__":
    timestamps_ms, x_values, y_values, z_values = load_accelerometer_axes(CSV_PATH)

    x_smooth = moving_average(x_values, SMOOTH_WINDOW)
    y_smooth = moving_average(y_values, SMOOTH_WINDOW)
    z_smooth = moving_average(z_values, SMOOTH_WINDOW)

    start_ms = timestamps_ms[0]
    x_seconds = [(ts - start_ms) / 1000.0 for ts in timestamps_ms]

    fig, ax = plt.subplots(figsize=(100, 6))
    ax.plot(x_seconds, x_smooth, color=COLORS["x"], linewidth=1.2, label="X axis")
    ax.plot(x_seconds, y_smooth, color=COLORS["y"], linewidth=1.2, label="Y axis")
    ax.plot(x_seconds, z_smooth, color=COLORS["z"], linewidth=1.2, label="Z axis")

    ax.set_title("Accelerometer Axes — sensor_data_20260607_215226")
    ax.set_xlabel("Seconds since start")
    ax.set_ylabel("Acceleration (m/s²)")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=160)
    plt.close(fig)

    print(f"Saved plot to: {OUTPUT_PATH}")
