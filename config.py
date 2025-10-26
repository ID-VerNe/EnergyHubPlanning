"""
Dynamic configuration loader for the MES optimization model.

This module loads parameters from a specified YAML file and makes them available
as module-level variables for other scripts to import and use.
"""
import yaml

# --- Module-level variables to hold the loaded configuration ---
# These will be populated by the load_config function.

# Simulation Control
NUM_DAYS = 8

# Economic Parameters
INTEREST_RATE = 0.08
GAS_PRICE_MULTIPLIER = 1.0

# Cost Parameters
SHED_COST_PER_MWH = {}

# Component Investment Costs
INVESTMENT_COSTS = {}

# Component Lifetimes
LIFETIMES = {}

# Component Base Capacities
BASE_CAPACITIES = {}

# Component Technical Parameters
COMPONENT_PARAMS = {}

def load_config(config_path: str):
    """
    Loads configuration from a YAML file and populates the module-level variables.

    Args:
        config_path: The absolute or relative path to the YAML configuration file.
    """
    global NUM_DAYS, INTEREST_RATE, GAS_PRICE_MULTIPLIER, SHED_COST_PER_MWH, \
           INVESTMENT_COSTS, LIFETIMES, BASE_CAPACITIES, COMPONENT_PARAMS

    print(f"--- Loading configuration from: {config_path} ---")
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[ERROR] Configuration file not found at: {config_path}")
        raise
    except Exception as e:
        print(f"[ERROR] Failed to load or parse YAML file: {e}")
        raise

    # Populate module variables from the loaded data
    sim_control = config_data.get('simulation_control', {})
    NUM_DAYS = sim_control.get('num_days', 8)

    econ_params = config_data.get('economic_parameters', {})
    INTEREST_RATE = econ_params.get('interest_rate', 0.08)
    GAS_PRICE_MULTIPLIER = econ_params.get('gas_price_multiplier', 1.0)

    cost_params = config_data.get('cost_parameters', {})
    SHED_COST_PER_MWH = cost_params.get('shed_cost_per_mwh', {})

    INVESTMENT_COSTS = config_data.get('investment_costs', {})
    LIFETIMES = config_data.get('lifetimes', {})
    BASE_CAPACITIES = config_data.get('base_capacities', {})
    COMPONENT_PARAMS = config_data.get('component_params', {})

    print("Configuration loaded successfully.")

# Example of loading a default config if this file is run directly (optional)
if __name__ == '__main__':
    # This part is for testing the loader itself.
    # In the actual application, run_analysis.py will call load_config.
    try:
        load_config('configs/1_baseline.yaml')
        print("\n--- Test Load Results ---")
        print(f"Number of days: {NUM_DAYS}")
        print(f"Shedding cost for electricity: {SHED_COST_PER_MWH['elec']}")
        print(f"Investment cost for CHP_A: {INVESTMENT_COSTS['CHP_A']}")
    except Exception as e:
        print(f"Test load failed: {e}")