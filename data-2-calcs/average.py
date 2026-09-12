import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

MAX_ERROR_PLOT = 1.25

# Load data
df = pd.read_csv("combined_heel_strikes.csv")
# Drop the first row which has NaN for time_to_prev_strike_sec
df = df.dropna(subset=['time_to_prev_strike_sec']).copy()
df = df.iloc[5:]
df.reset_index(drop=True, inplace=True)

# Target variable to predict
y = df['time_to_prev_strike_sec']

N_values = [2, 3, 4, 5, 7, 10, 15, 20, 30, 50, 70]  # Different numbers of previous steps to consider for prediction



# Helper functions for the moving average types
# =====================================================================

# Simple Moving Average
def sma(series, n):
    return series.rolling(window=n).mean()


# Weighted Moving Average
def wma(series, n):
    weights = np.arange(1, n + 1)
    return series.rolling(window=n).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)


# Hull Moving Average
def hma(series, n):
    half_n = max(1, int(n / 2))
    sqrt_n = max(1, int(np.sqrt(n)))
    wma_half = wma(series, half_n)
    wma_full = wma(series, n)
    diff = 2 * wma_half - wma_full
    return wma(diff, sqrt_n)


# Arnaud Legoux Moving Average
def alma(series, n, offset=0.85, sigma=6):
    m = offset * (n - 1)
    s = n / sigma
    weights = np.array([np.exp(-((i - m) ** 2) / (2 * s * s)) for i in range(n)])
    weights /= weights.sum()
    return series.rolling(window=n).apply(lambda x: np.dot(x, weights), raw=True)


def ema(series, n):
    return series.ewm(span=n, adjust=False).mean()



# Evaluation
# Reused for SMA, EMA, WMA, HMA, ALMA
def evaluate(method_name, pred_func):
    method_results = []
    method_predictions = {}

    for n in N_values:
        # Compute the moving average, then shift by 1
        # so that the prediction for time t only uses data up to t-1
        pred = pred_func(y, n).shift(1)
        method_predictions[n] = pred

        # Calculate errors (only where predictions are not NaN)
        valid_idx = pred.dropna().index
        y_actual = y.loc[valid_idx]
        y_pred = pred.loc[valid_idx]

        mae = np.mean(np.abs(y_actual - y_pred))
        rmse = np.sqrt(np.mean((y_actual - y_pred) ** 2))

        method_results.append({'N': n, 'MAE': mae, 'RMSE': rmse})

    method_results_df = pd.DataFrame(method_results)
    print(f"\n{method_name} results:")
    print(method_results_df)

    return method_results_df, method_predictions


# Run the evaluation for every method
methods = {
    'SMA': sma,
    'EMA': ema,
    'WMA': wma,
    'HMA': hma,
    'ALMA': alma,
}

all_results = {}
all_predictions = {}

for method_name, pred_func in methods.items():
    results_df, predictions = evaluate(method_name, pred_func)
    all_results[method_name] = results_df
    all_predictions[method_name] = predictions


sma_results_df, sma_predictions = all_results['SMA'], all_predictions['SMA']
ema_results_df, ema_predictions = all_results['EMA'], all_predictions['EMA']
wma_results_df, wma_predictions = all_results['WMA'], all_predictions['WMA']
hma_results_df, hma_predictions = all_results['HMA'], all_predictions['HMA']
alma_results_df, alma_predictions = all_results['ALMA'], all_predictions['ALMA']


# Plot 1: Errors Comparison for ALL methods
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
axes = axes.flatten()

x_pos = np.arange(len(N_values))
width = 0.35

for ax, (method_name, results_df) in zip(axes, all_results.items()):
    ax.bar(x_pos - width / 2, results_df['MAE'], width, label='MAE (Mean Absolute Error)')
    ax.bar(x_pos + width / 2, results_df['RMSE'], width, label='RMSE (Root Mean Square Error)')

    ax.set_xlabel('Number of Previous Steps (N)')
    ax.set_ylabel('Error in Seconds')
    ax.set_title(f'Prediction Error by Amount of Previous Steps Used ({method_name})')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(N_values)
    ax.set_ylim(0, MAX_ERROR_PLOT)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)

# Hide any unused subplot slots
for ax in axes[len(all_results):]:
    ax.axis('off')

plt.tight_layout()
plt.savefig('error_comparison_all_methods.png')
plt.show()


# Plot 2: Actual vs Predictions for ALL methods
fig, axes = plt.subplots(2, 3, figsize=(20, 10))
axes = axes.flatten()

subset_end = 100  # Adjust if necessary to see detail
colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta']

for ax, (method_name, predictions) in zip(axes, all_predictions.items()):
    ax.plot(y.index[:subset_end], y.iloc[:subset_end], label='Actual', color='black', linewidth=2, marker='o',
            markersize=4)

    for i, n in enumerate(N_values):
        ax.plot(y.index[:subset_end], predictions[n].iloc[:subset_end], label=f'Predicted (N={n})',
                color=colors[i % len(colors)], linestyle='--', alpha=0.7)

    ax.set_xlabel('Step Index')
    ax.set_ylabel('Time to Previous Strike (Seconds)')
    ax.set_title(f'Actual vs Predicted Values (First 100 Steps, {method_name})')
    ax.legend(fontsize=7)
    ax.grid(True, linestyle=':', alpha=0.6)

# Hide any unused subplot slots
for ax in axes[len(all_predictions):]:
    ax.axis('off')

plt.tight_layout()
plt.savefig('predictions_timeseries_all_methods.png')
plt.show()



# Combined summary of all methods (best MAE/RMSE per method)
summary_rows = []
for method_name, r_df in all_results.items():
    best_row = r_df.loc[r_df['MAE'].idxmin()]
    summary_rows.append({
        'Method': method_name,
        'Best N (by MAE)': int(best_row['N']),
        'MAE': best_row['MAE'],
        'RMSE': best_row['RMSE'],
    })

summary_df = pd.DataFrame(summary_rows)
print("\nSummary (best N per method by MAE):")
print(summary_df)