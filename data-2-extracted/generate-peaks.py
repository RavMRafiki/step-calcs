import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# 1. Load and prepare the data
df = pd.read_csv('sensor_data_20260607_215231.csv')
df_acc = df[df['sensor'] == 'Accelerometer'].copy()
df_acc.reset_index(drop=True, inplace=True)

# Convert timestamp to relative time in seconds
df_acc['time_sec'] = (df_acc['timestamp'] - df_acc['timestamp'].iloc[0]) / 1000

# 2. Isolate the impact signal (X-axis) and invert it 
# find_peaks looks for local maxima, so we invert the downward spikes
signal = df_acc['x'].values
inverted_signal = -signal

# 3. Find the peaks (heel strikes)
peaks, _ = find_peaks(inverted_signal, prominence=33, distance=80)

# 4. Extract the peak data and save to CSV
df_peaks = df_acc.iloc[peaks].copy()
# Select specific columns to output
df_peaks = df_peaks[['timestamp', 'time_sec', 'sensor', 'x', 'y', 'z']]

# Save directly to a new CSV file
df_peaks.to_csv('heel_strikes_detected_20260607_215231.csv', index=False)

# 5. Visualize and save the chart
plt.figure(figsize=(50, 6))
plt.plot(df_acc['time_sec'], signal, label='Accelerometer X-axis', color='black', linewidth=1)
plt.plot(df_acc['time_sec'].iloc[peaks], signal[peaks], "ro", label='Detected Ground Contact (Heel Strikes)')
plt.title("Walking Gait Analysis: Ground Contact Detection")
plt.xlabel("Time (seconds)")
plt.ylabel("Acceleration")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

# Save the plot as an image
plt.savefig('heel_strikes_chart_20260607_215231.png')