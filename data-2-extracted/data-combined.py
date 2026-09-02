# offset_sec = .3

import pandas as pd

# Load the two CSV files
df1 = pd.read_csv('heel_strikes_detected_20260607_215226.csv')
df2 = pd.read_csv('heel_strikes_detected_20260607_215231.csv')

df1['timestamp'] = df1['timestamp'] + 400

# Combine the dataframes
combined_df = pd.concat([df1, df2], ignore_index=True)

# Sort by timestamp to ensure chronological order
combined_df = combined_df.sort_values(by='timestamp').reset_index(drop=True)

# Recalculate relative time in seconds based on the earliest combined timestamp
combined_df['time_sec'] = (combined_df['timestamp'] - combined_df['timestamp'].iloc[0]) / 1000


combined_df['time_to_prev_strike_sec'] = combined_df['time_sec'].diff()
# Save to a new CSV file
combined_df.to_csv('combined_heel_strikes.csv', index=False)


import pandas as pd
import matplotlib.pyplot as plt

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
# Find the absolute earliest timestamp across both datasets so the chart starts at 0
t0 = min(df_acc1['timestamp'].min(), df_acc2['timestamp'].min())

# Convert all timestamps to relative time in seconds based on t0
df_acc1['time_sec'] = (df_acc2['timestamp'] - t0) / 1000
df_acc2['time_sec'] = (df_acc2['timestamp'] - t0) / 1000
df_peaks1['time_sec'] = (df_peaks2['timestamp'] - t0) / 1000
df_peaks2['time_sec'] = (df_peaks2['timestamp'] - t0) / 1000

# 4. Visualize and save the chart
# Using the ultra-wide figsize requested
plt.figure(figsize=(50, 6))

# Plot the raw signals
# Making the second line gray and slightly transparent so the chart isn't too chaotic
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