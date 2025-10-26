
'''
This script generates analysis plots from the batch simulation results.
It creates two main visualizations:
1. A dual-axis line chart showing the trade-off between annual cost and solve time
   as the number of representative days increases.
2. A heatmap illustrating the 'tipping point' for gas technology viability by
   plotting gas import volume against gas price and investment cost multipliers.
'''
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Configuration ---
RESULTS_DIR = 'batch_results'
OUTPUT_DIR = 'plots'
DAYS_SWEEP_FILE = os.path.join(RESULTS_DIR, 'days_sweep_results.csv')
GAS_SWEEP_FILE = os.path.join(RESULTS_DIR, 'gas_viability_sweep_results.csv')

# --- Helper Functions ---
def ensure_dir(directory):
    """Creates a directory if it does not exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def plot_days_sweep_analysis():
    """Generates and saves the plot for the typical days analysis."""
    print(f"--- Generating plot for: {DAYS_SWEEP_FILE} ---")
    if not os.path.exists(DAYS_SWEEP_FILE):
        print(f"ERROR: File not found - {DAYS_SWEEP_FILE}")
        return

    df = pd.read_csv(DAYS_SWEEP_FILE)
    df = df.sort_values(by='num_days').reset_index()

    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Plot Total Annual Cost on the left y-axis
    color = 'tab:blue'
    ax1.set_xlabel('Number of Representative Days', fontsize=16)
    ax1.set_ylabel('Total Annual Cost (HKD 100M)', color=color, fontsize=16)
    ax1.plot(df['num_days'], df['total_annual_cost'] / 1e8, color=color, marker='o', linestyle='-', label='Total Annual Cost')
    ax1.tick_params(axis='y', labelcolor=color, labelsize=12)
    ax1.tick_params(axis='x', labelsize=12)
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

    # Create a second y-axis for Solve Time
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Solve Time (s)', color=color, fontsize=16)
    ax2.plot(df['num_days'], df['solve_time'], color=color, marker='s', linestyle='--', label='Solve Time')
    ax2.tick_params(axis='y', labelcolor=color, labelsize=12)

    # Title and layout
    plt.title('Impact of Representative Days on Cost and Solve Time', fontsize=20)
    fig.tight_layout()  # Adjust layout to make room for labels
    
    # Add a single legend
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.15), fancybox=True, shadow=True, ncol=2, fontsize=14)

    # Save the figure
    output_path = os.path.join(OUTPUT_DIR, 'days_sweep_analysis.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {output_path}")
    plt.close()

def plot_gas_viability_heatmap():
    """Generates and saves the heatmap for the gas viability analysis."""
    print(f"\n--- Generating heatmap for: {GAS_SWEEP_FILE} ---")
    if not os.path.exists(GAS_SWEEP_FILE):
        print(f"ERROR: File not found - {GAS_SWEEP_FILE}")
        return

    df = pd.read_csv(GAS_SWEEP_FILE)

    # Pivot the data to create a matrix for the heatmap
    # We use gas import as the value to color the cells
    df['gas_import_1e5_mwh'] = df['gas_import_mwh'] / 1e5 # Scale down the data
    heatmap_data = df.pivot_table(
        index='gas_invest_multiplier',
        columns='gas_price_multiplier',
        values='gas_import_1e5_mwh' # Use the scaled data for values
    )
    # Sort the axes for a correct representation
    heatmap_data = heatmap_data.sort_index(ascending=False)
    heatmap_data = heatmap_data.sort_index(axis=1, ascending=True)

    plt.figure(figsize=(12, 9))
    
    # Create the heatmap using seaborn
    sns.heatmap(
        heatmap_data,
        annot=True,       # Annotate cells with the gas import value
        annot_kws={"size": 12},
        fmt='.1f',        # Format annotations to one decimal place
        cmap='viridis', 
        linewidths=.5,
        cbar_kws={'label': 'Total Annual Gas Import (100 GWh/year)'} # Update color bar label
    )

    # Title and labels
    # plt.title('Gas Technology Viability: Tipping Point Analysis', fontsize=20)
    plt.xlabel('Gas Price Multiplier (Relative to Baseline)', fontsize=16)
    plt.ylabel('Gas Investment Cost Multiplier (Relative to Baseline)', fontsize=16)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    
    # Save the figure
    output_path = os.path.join(OUTPUT_DIR, 'gas_viability_heatmap.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {output_path}")
    plt.close()

if __name__ == "__main__":
    ensure_dir(OUTPUT_DIR)
    plot_days_sweep_analysis()
    plot_gas_viability_heatmap()
