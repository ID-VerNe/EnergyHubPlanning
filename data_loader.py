# Copyright (c) 2025 VerNe.
# All rights reserved.
#
# This code is for personal academic use only.
# Unauthorized use, copying, or distribution of this code is strictly prohibited.

"""
Data loading and processing for the MES optimization model.

This module reads the time series data from data.csv, handles typical day
selection, and prepares the data for the optimization model.
"""
import pandas as pd
import numpy as np

# Import configuration
import config

def load_and_prepare_data():
    """
    Loads time series data, selects representative days, and calculates weights.

    Returns:
        A tuple containing:
        - pd.DataFrame: DataFrame with data for the selected typical days.
        - np.ndarray: An array of weights for each typical day.
    """
    print("--- Loading and Preparing Data ---")
    
    # Load the full 365-day time series data
    try:
        full_data = pd.read_csv('data/data.csv', index_col=0, parse_dates=True)
    except FileNotFoundError:
        print("Error: 'data/data.csv' not found. Please ensure the data file exists.")
        return None, None

    # Apply gas price multiplier from config
    if 'Gas_Price' in full_data.columns:
        full_data['Gas_Price'] *= config.GAS_PRICE_MULTIPLIER
    
    # --- Typical Day Selection (Simplified Method) ---
    # This is a simplified placeholder for a more advanced clustering algorithm like tsam.
    # It selects days evenly spaced throughout the year.
    num_total_days = len(full_data) // 24
    num_typical_days = config.NUM_DAYS

    if num_typical_days > num_total_days:
        raise ValueError(f"NUM_DAYS ({num_typical_days}) cannot be greater than the total number of days in the dataset ({num_total_days}).")

    # Get the corresponding hourly indices for the selected days
    day_indices = np.linspace(0, num_total_days - 1, num_typical_days, dtype=int)
    hour_indices = []
    for day_idx in day_indices:
        hour_indices.extend(range(day_idx * 24, (day_idx + 1) * 24))

    typical_days_data = full_data.iloc[hour_indices].copy()

    # --- Calculate Weights ---
    # In this simplified method, each selected day represents an equal number of days from the year.
    # The total weight should sum to the total number of days in the year.
    weight = num_total_days / num_typical_days
    day_weights = np.full(num_typical_days, weight)

    print(f"Selected {num_typical_days} representative days from {num_total_days} total days.")
    print(f"Each representative day has a weight of: {weight:.2f}")

    return typical_days_data, day_weights

if __name__ == '__main__':
    # Test the data loader
    typical_data, weights = load_and_prepare_data()
    if typical_data is not None:
        print("\nData loaded successfully!")
        print("Shape of typical days data:", typical_data.shape)
        print("Data columns:", typical_data.columns.tolist())
        print("Day weights:", weights)
        print("Sum of weights:", np.sum(weights))
        print("\nFirst 5 rows of data:")
        print(typical_data.head())