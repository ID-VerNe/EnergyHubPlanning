# Copyright (c) 2025 VerNe.
# All rights reserved.
#
# This code is for personal academic use only.
# Unauthorized use, copying, or distribution of this code is strictly prohibited.

'''
This script automates running batch analyses for the MES planning project.
It systematically runs simulations for two key questions:
1. The impact of the number of representative days.
2. The conditions under which gas technology becomes viable (2D sweep of gas price and investment cost).

The script works by:
1. Reading a baseline configuration file.
2. Programmatically generating temporary config files for each experimental run.
3. Calling the main `run_optimization` function from `run_analysis.py`.
4. Parsing the key results from the generated summary text files.
5. Aggregating all results into clean CSV files for easy plotting and analysis.
'''
import os
import yaml
import pandas as pd
import time
import re
import copy
from run_analysis import run_optimization

# --- Configuration ---
BASELINE_CONFIG_PATH = 'configs/1_baseline.yaml'
TEMP_CONFIG_DIR = 'configs/temp'
RESULTS_DIR = 'batch_results'


# --- Helper Functions ---
def ensure_dir(directory):
    """Creates a directory if it does not exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)


def parse_summary_file(file_path):
    """
    Parses a summary.txt file to extract key metrics.
    Returns a dictionary of results.
    """
    results = {}
    if not os.path.exists(file_path):
        results['error'] = 'File not found'
        return results

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        results['error'] = f'Could not read file: {e}'
        return results

    def find_value(pattern, text):
        match = re.search(pattern, text)
        if not match:
            return 0.0
        try:
            value_str = match.group(1).replace(',', '')
            return float(value_str)
        except (ValueError, IndexError):
            return 0.0

    results['total_annual_cost'] = find_value(r"Total Annual Cost: ([\d,.-]+)", content)
    results['investment_cost'] = find_value(r"Annualized Investment Cost: ([\d,.-]+)", content)
    results['operational_cost'] = find_value(r"Total Annual Operational Cost: ([\d,.-]+)", content)
    results['gas_import_mwh'] = find_value(r"Total Gas Import: ([\d,.-]+)", content)
    results['elec_import_mwh'] = find_value(r"Total Elec Import: ([\d,.-]+)", content)
    results['solve_time'] = find_value(r"Total Time: ([\d,.-]+)s", content)

    gas_invest_cap = 0
    gas_components = ['CHP_A', 'CHP_B', 'ICE', 'Gas_Boiler']
    for comp in gas_components:
        pattern = comp + r": \d+ units? => Capacity: ([\d,.-]+) MW"
        gas_invest_cap += find_value(pattern, content)
    results['gas_invested_capacity_mw'] = gas_invest_cap
    return results


def run_days_sweep():
    """
    Runs the analysis for Question 2: Impact of the number of typical days.
    """
    print(">>> Starting Batch Analysis: Impact of Typical Days")
    days_to_test = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 30, 50]
    all_results = []

    try:
        with open(BASELINE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            base_config = yaml.safe_load(f)
    except Exception as e:
        print(f"FATAL: Could not read baseline config: {e}")
        return

    for days in days_to_test:
        scenario_name = f"days_{days}"
        print(f"--- Running scenario: {scenario_name}")
        temp_config = copy.deepcopy(base_config)
        temp_config['simulation_control']['num_days'] = days
        temp_config_path = os.path.join(TEMP_CONFIG_DIR, f"{scenario_name}.yaml")

        try:
            with open(temp_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(temp_config, f)

            run_optimization(temp_config_path)

            summary_path = os.path.join('results', f"{scenario_name}_summary.txt")
            result = parse_summary_file(summary_path)
            result['num_days'] = days
            all_results.append(result)
        except Exception as e:
            print(f"ERROR running scenario {scenario_name}: {e}")

    if all_results:
        results_df = pd.DataFrame(all_results)
        output_path = os.path.join(RESULTS_DIR, 'days_sweep_results.csv')
        results_df.to_csv(output_path, index=False)
        print(f"\nDays sweep analysis complete. Results saved to {output_path}")


def run_gas_viability_sweep():
    """
    Runs the analysis for Question 5: Gas price and investment cost sweep.
    """
    print("\n>>> Starting Batch Analysis: Gas Viability (2D Sweep)")
    gas_price_multipliers = [1.0, 0.9, 0.8,0.7, 0.6, 0.5, 0.4,0.3, 0.2, 0.1, 0]
    gas_invest_multipliers = [1.0, 0.9, 0.8,0.7, 0.6, 0.5, 0.4,0.3, 0.2, 0.1, 0]
    all_results = []

    try:
        with open(BASELINE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            base_config = yaml.safe_load(f)
    except Exception as e:
        print(f"FATAL: Could not read baseline config: {e}")
        return

    original_gas_investments = {
        'CHP_A': base_config['investment_costs']['CHP_A'],
        'CHP_B': base_config['investment_costs']['CHP_B'],
        'ICE': base_config['investment_costs']['ICE'],
        'Gas_Boiler': base_config['investment_costs']['Gas_Boiler'],
    }

    for p_mult in gas_price_multipliers:
        for i_mult in gas_invest_multipliers:
            scenario_name = f"gas_p{int(p_mult * 100)}_i{int(i_mult * 100)}"
            print(f"--- Running scenario: {scenario_name}")
            temp_config = copy.deepcopy(base_config)
            temp_config['economic_parameters']['gas_price_multiplier'] = p_mult

            for device, original_cost in original_gas_investments.items():
                if device in temp_config['investment_costs']:
                    temp_config['investment_costs'][device] = original_cost * i_mult

            temp_config_path = os.path.join(TEMP_CONFIG_DIR, f"{scenario_name}.yaml")

            try:
                with open(temp_config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(temp_config, f)
                run_optimization(temp_config_path)
                summary_path = os.path.join('results', f"{scenario_name}_summary.txt")
                result = parse_summary_file(summary_path)
                result['gas_price_multiplier'] = p_mult
                result['gas_invest_multiplier'] = i_mult
                all_results.append(result)
            except Exception as e:
                print(f"ERROR running scenario {scenario_name}: {e}")

    if all_results:
        results_df = pd.DataFrame(all_results)
        output_path = os.path.join(RESULTS_DIR, 'gas_viability_sweep_results.csv')
        results_df.to_csv(output_path, index=False)
        print(f"\nGas viability sweep complete. Results saved to {output_path}")


if __name__ == "__main__":
    ensure_dir(TEMP_CONFIG_DIR)
    ensure_dir(RESULTS_DIR)
    run_days_sweep()
    # run_gas_viability_sweep()
    print("\n\nAll batch analyses finished.")
