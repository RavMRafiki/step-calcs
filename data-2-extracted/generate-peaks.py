import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# Both recordings are processed with the SAME physical parameters.
# Note the refractory period is given in milliseconds, not in samples: the two
# phones log at different rates (~51.5 Hz vs 200 Hz), so a fixed `distance=80`
# would mean 1553 ms on one phone and 400 ms on the other.
FILES = [
    'sensor_data_20260607_215226.csv',
    'sensor_data_20260607_215231.csv',
]
PROMINENCE = 25      # minimum depth of a downward spike to count as a strike
MIN_GAP_MS = 700     # refractory period; shortest observed stride is ~970 ms


def analyse(path):
    tag = path.replace('sensor_data_', '').replace('.csv', '')

    # 1. Load and prepare the data
    df = pd.read_csv(path)
    df_acc = df[df['sensor'] == 'Accelerometer'].copy()
    df_acc.reset_index(drop=True, inplace=True)

    # Convert timestamp to relative time in seconds
    df_acc['time_sec'] = (df_acc['timestamp'] - df_acc['timestamp'].iloc[0]) / 1000

    # 2. Isolate the impact signal (X-axis) and invert it
    # find_peaks looks for local maxima, so we invert the downward spikes
    signal = df_acc['x'].values
    inverted_signal = -signal

    # 3. Find the peaks (heel strikes)
    # Convert the refractory period to samples using this file's own rate
    fs = len(df_acc) / (df_acc['time_sec'].iloc[-1] - df_acc['time_sec'].iloc[0])
    distance = max(1, int(round(MIN_GAP_MS * fs / 1000)))
    peaks, _ = find_peaks(inverted_signal, prominence=PROMINENCE, distance=distance)

    # 4. Extract the peak data and save to CSV
    df_peaks = df_acc.iloc[peaks].copy()
    # Select specific columns to output
    df_peaks = df_peaks[['timestamp', 'time_sec', 'sensor', 'x', 'y', 'z']]

    # Save directly to a new CSV file
    df_peaks.to_csv('heel_strikes_detected_%s.csv' % tag, index=False)

    # 5. Visualize and save the chart
    plt.figure(figsize=(50, 6))
    plt.plot(df_acc['time_sec'], signal, label='Accelerometer X-axis', color='black', linewidth=1)
    plt.plot(df_acc['time_sec'].iloc[peaks], signal[peaks], "ro", label='Detected Ground Contact (Heel Strikes)')
    plt.title("Walking Gait Analysis: Ground Contact Detection (%s)" % tag)
    plt.xlabel("Time (seconds)")
    plt.ylabel("Acceleration")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save the plot as an image
    plt.savefig('heel_strikes_chart_%s.png' % tag)
    plt.close()

    strides = np.diff(df_peaks['timestamp'].values)
    print('%s: %.1f Hz -> distance=%d samples (%d ms) | %d strikes | stride median %.0f ms, min %.0f ms'
          % (tag, fs, distance, MIN_GAP_MS, len(df_peaks), np.median(strides), strides.min()))


for path in FILES:
    analyse(path)
