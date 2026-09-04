import pandas as pd
import matplotlib.pyplot as plt

# Clock offset between the two phones (ms), applied to phone 215226 everywhere:
# both in the combined CSV and on the chart.
OFFSET_MS = 400

# 1. Load the raw sensor data
df_raw1 = pd.read_csv('sensor_data_20260607_215226.csv')
df_raw2 = pd.read_csv('sensor_data_20260607_215231.csv')

# Filter for just the Accelerometer data
df_acc1 = df_raw1[df_raw1['sensor'] == 'Accelerometer'].copy()
df_acc2 = df_raw2[df_raw2['sensor'] == 'Accelerometer'].copy()

# 2. Load the pre-detected heel strike data
df_peaks1 = pd.read_csv('heel_strikes_detected_20260607_215226.csv')
df_peaks2 = pd.read_csv('heel_strikes_detected_20260607_215231.csv')

# 3. Synchronize timelines
# Shift phone 1 onto phone 2's clock (raw signal and peaks alike)
df_acc1['timestamp'] = df_acc1['timestamp'] + OFFSET_MS
df_peaks1['timestamp'] = df_peaks1['timestamp'] + OFFSET_MS

# Find the absolute earliest timestamp across both datasets so the chart starts at 0
t0 = min(df_acc1['timestamp'].min(), df_acc2['timestamp'].min())

# Convert all timestamps to relative time in seconds based on t0.
# NOTE: use .values so pandas does not align on the row index - the two
# recordings have different sampling rates (51.5 Hz vs 200 Hz) and different
# row counts, so index alignment would silently paste the wrong times in.
df_acc1['time_sec'] = (df_acc1['timestamp'].values - t0) / 1000
df_acc2['time_sec'] = (df_acc2['timestamp'].values - t0) / 1000
df_peaks1['time_sec'] = (df_peaks1['timestamp'].values - t0) / 1000
df_peaks2['time_sec'] = (df_peaks2['timestamp'].values - t0) / 1000

# 4. Build the combined heel-strike table on that same timeline
combined_df = pd.concat([df_peaks1, df_peaks2], ignore_index=True)
combined_df = combined_df.sort_values(by='timestamp').reset_index(drop=True)
combined_df['time_to_prev_strike_sec'] = combined_df['time_sec'].diff()
combined_df.to_csv('combined_heel_strikes.csv', index=False)

# 5. Visualize and save the chart
# Using the ultra-wide figsize requested
plt.figure(figsize=(50, 6))

# Plot the raw signals
plt.plot(df_acc1['time_sec'], df_acc1['x'], label='Accelerometer X-axis (215226)', color='pink', linewidth=1)
plt.plot(df_acc2['time_sec'], df_acc2['x'], label='Accelerometer X-axis (215231)', color='lightblue', linewidth=1, alpha=0.7)

# Plot the detected ground contacts (heel strikes)
plt.plot(df_peaks1['time_sec'], df_peaks1['x'], "ro", label='Heel Strikes (215226)')
plt.plot(df_peaks2['time_sec'], df_peaks2['x'], "bo", label='Heel Strikes (215231)')

plt.title("Combined Walking Gait Analysis: Ground Contact Detection")
plt.xlabel("Time (seconds)")
plt.ylabel("Acceleration")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

# Save the plot as an image
plt.savefig('combined_heel_strikes_wide_chart.png')