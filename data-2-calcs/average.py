import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv("combined_heel_strikes.csv")
# Drop the first row which has NaN for time_to_prev_strike_sec
df = df.dropna(subset=['time_to_prev_strike_sec']).copy()
df = df.iloc[5:]
df.reset_index(drop=True, inplace=True)

# Target variable to predict
y = df['time_to_prev_strike_sec']

N_values = [2, 3, 4, 5, 7, 10, 15, 20, 30, 50, 70]  # Different numbers of previous steps to consider for prediction
results = []
predictions = {}

for n in N_values:
    # Calculate rolling mean of the past 'n' steps
    # We shift by 1 because the prediction for time t should only use data up to t-1
    pred = y.rolling(window=n).mean().shift(1)
    predictions[n] = pred
    
    # Calculate errors (only where predictions are not NaN)
    valid_idx = pred.dropna().index
    y_actual = y.loc[valid_idx]
    y_pred = pred.loc[valid_idx]
    
    mae = np.mean(np.abs(y_actual - y_pred))
    rmse = np.sqrt(np.mean((y_actual - y_pred)**2))
    
    results.append({'N': n, 'MAE': mae, 'RMSE': rmse})

results_df = pd.DataFrame(results)
print(results_df)

# Plot 1: Errors Comparison
plt.figure(figsize=(10, 5))
x_pos = np.arange(len(N_values))
width = 0.35

plt.bar(x_pos - width/2, results_df['MAE'], width, label='MAE (Mean Absolute Error)')
plt.bar(x_pos + width/2, results_df['RMSE'], width, label='RMSE (Root Mean Square Error)')

plt.xlabel('Number of Previous Steps (N)')
plt.ylabel('Error in Seconds')
plt.title('Prediction Error by Amount of Previous Steps Used')
plt.xticks(x_pos, N_values)
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('error_comparison.png')
plt.show()

# Plot 2: Actual vs Predictions (subset for clarity)
plt.figure(figsize=(14, 6))
subset_end = 100 # Adjust if necessary to see detail
plt.plot(y.index[:subset_end], y.iloc[:subset_end], label='Actual', color='black', linewidth=2, marker='o', markersize=4)

colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta']
for i, n in enumerate(N_values):
    plt.plot(y.index[:subset_end], predictions[n].iloc[:subset_end], label=f'Predicted (N={n})', color=colors[i], linestyle='--', alpha=0.7)

plt.xlabel('Step Index')
plt.ylabel('Time to Previous Strike (Seconds)')
plt.title('Actual vs Predicted Values (First 100 Steps)')
plt.legend()
plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig('predictions_timeseries.png')
plt.show()