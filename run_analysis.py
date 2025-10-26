# Copyright (c) 2025 VerNe.
# All rights reserved.
#
# This code is for personal academic use only.
# Unauthorized use, copying, or distribution of this code is strictly prohibited.

"""
Main script to run the MES (Multi-Energy System) optimization analysis.
This script replicates the logic from the reference notebook using the pymeshub structure,
and adds detailed result logging to text and CSV files.
"""
import time
import cvxpy as cp
import numpy as np
import pandas as pd
import os

import config
import utils
from data_loader import load_and_prepare_data
from mes_model import build_mes_model
from pymeshub.components.storage import Storage

def run_optimization(config_path: str):
    print("========= Starting MES Optimization Analysis ==========")
    start_time = time.time()

    # 0. Load Configuration FIRST
    # This is the critical fix: load config before any other steps.
    try:
        config.load_config(config_path)
    except Exception as e:
        print(f"FATAL: Failed to load configuration file {config_path}. Error: {e}")
        return

    # 1. Load Data and Build Model
    typical_data, day_weights = load_and_prepare_data()
    if typical_data is None:
        return
    hub = build_mes_model()

    for comp in hub.components.values():
        if comp.name in config.BASE_CAPACITIES:
            if isinstance(config.BASE_CAPACITIES[comp.name], dict):
                comp.power_base = config.BASE_CAPACITIES[comp.name]['power']
                comp.cap_base = config.BASE_CAPACITIES[comp.name]['capacity']
            else:
                comp.base_capacity = config.BASE_CAPACITIES[comp.name]

    branch_name_to_idx = {name: i for i, name in enumerate(hub.global_branches)}
    converters = [c for c in hub.components.values() if not isinstance(c, Storage)]
    storages = [c for c in hub.components.values() if isinstance(c, Storage)]
    num_converters, num_storages = len(converters), len(storages)
    num_hours, num_days = 24, len(day_weights)

    # 2. Define CVXPY Variables
    print("--- Defining Optimization Variables ---")
    invest_units_conv = cp.Variable(num_converters, integer=True, name="ConvInvestUnits")
    invest_units_stor = cp.Variable(num_storages, integer=True, name="StorInvestUnits")
    V = cp.Variable((len(hub.global_branches), num_days * num_hours), nonneg=True, name="EnergyFlows")
    soc = cp.Variable((num_storages, num_days * num_hours), nonneg=True, name="StateOfCharge")
    charge_flag = cp.Variable((num_storages, num_days * num_hours), boolean=True, name="ChargeFlag")
    discharge_flag = cp.Variable((num_storages, num_days * num_hours), boolean=True, name="DischargeFlag")
    shed_elec = cp.Variable(num_days * num_hours, nonneg=True, name="ShedElec")
    shed_heat = cp.Variable(num_days * num_hours, nonneg=True, name="ShedHeat")
    shed_cool = cp.Variable(num_days * num_hours, nonneg=True, name="ShedCool")

    # 3. Define Constraints
    print("--- Defining Constraints ---")
    constraints = [invest_units_conv >= 0, invest_units_stor >= 0]

    def get_total_flow(indices):
        if not indices: return 0
        return cp.sum(V[indices, :], axis=0)

    # Define Total Import/Export Flows FIRST
    gas_flow_total = get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('Gas_Import_out_to_')])
    elec_flow_total = get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('Elec_Import_out_to_')])

    # Node Balance Constraints
    elec_gen = get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('Elec_Import_out_to')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('CHP_A_elec_out_to')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('CHP_B_elec_out_to')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('ICE_elec_out_to')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('Elec_Storage_energy_out_to')])
    elec_cons = get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.endswith('_to_Elec_Boiler_elec_in')]) + \
                get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.endswith('_to_Heat_Pump_A_elec_in')]) + \
                get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.endswith('_to_Heat_Pump_B_elec_in')]) + \
                get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.endswith('_to_CERG_A_elec_in')]) + \
                get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.endswith('_to_CERG_B_elec_in')]) + \
                get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.endswith('_to_Elec_Storage_energy_in')])
    constraints.append(elec_gen == elec_cons + typical_data['elec_load(MW)'].values - shed_elec)

    heat_gen = get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('Gas_Boiler_heat_out_to')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('Elec_Boiler_heat_out_to')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('CHP_A_heat_out_to')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('CHP_B_heat_out_to')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('ICE_heat_out_to')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('Heat_Pump_A_heat_out_to')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('Heat_Pump_B_heat_out_to')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('Heat_Storage_energy_out_to')])
    heat_cons = get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.endswith('_to_WARP_heat_in')]) + \
                get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.endswith('_to_Heat_Storage_energy_in')])
    constraints.append(heat_gen == heat_cons + typical_data['heating_load(MW)'].values - shed_heat)

    cool_gen = get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('CERG_A_cool_out_to')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('CERG_B_cool_out_to')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('WARP_cool_out_to')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith('Cooling_Storage_energy_out_to')])
    cool_cons = get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.endswith('_to_Cooling_Storage_energy_in')])
    constraints.append(cool_gen == cool_cons + typical_data['cooling_load(MW)'].values - shed_cool)

    # Correctly link gas supply to gas consumption
    gas_cons = get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.endswith('_to_CHP_A_fuel_in')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.endswith('_to_CHP_B_fuel_in')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.endswith('_to_ICE_fuel_in')]) + \
               get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.endswith('_to_Gas_Boiler_fuel_in')])
    constraints.append(gas_flow_total == gas_cons)

    # Internal Component Physics & Capacity
    for i, conv in enumerate(converters):
        params = config.COMPONENT_PARAMS[conv.name]
        input_port = list(conv.input_ports.keys())[0]
        input_flow = get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.endswith(f'_to_{conv.name}_{input_port}')])
        constraints.append(input_flow <= invest_units_conv[i] * conv.base_capacity)
        for j, (out_port, out_type) in enumerate(conv.output_ports.items()):
            output_flow = get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith(f'{conv.name}_{out_port}_to_')])
            
            # --- ROBUST FIX: Explicitly map ports to efficiency params ---
            eff = 0
            # For multi-output components, map ports to params by name
            if conv.__class__.__name__ == 'CHPBackPressure':
                if out_port == 'elec_out':
                    eff = params['eta_w']
                elif out_port == 'heat_out':
                    eff = params['eta_q']
            # For single-output components, the logic is simple
            else:
                # The first key in the params dict is the correct one
                eff_key = list(params.keys())[0]
                eff = params[eff_key]
            
            constraints.append(output_flow == input_flow * eff)

    # Storage Constraints
    for i, stor in enumerate(storages):
        charge_flow = get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.endswith(f'_to_{stor.name}_energy_in')])
        discharge_flow = get_total_flow([idx for name, idx in branch_name_to_idx.items() if name.startswith(f'{stor.name}_energy_out_to_')])
        constraints += [charge_flow <= invest_units_stor[i] * stor.power_base, discharge_flow <= invest_units_stor[i] * stor.power_base, soc[i, :] <= invest_units_stor[i] * stor.cap_base, charge_flow <= charge_flag[i, :] * 1e5, discharge_flow <= discharge_flag[i, :] * 1e5, charge_flag[i, :] + discharge_flag[i, :] <= 1]
        eta_c, eta_d = stor.get_parameter('eta_c'), stor.get_parameter('eta_d')
        for d in range(num_days):
            day_slice = range(d * num_hours, (d + 1) * num_hours)
            for t_idx, t in enumerate(day_slice):
                prev_t = day_slice[t_idx - 1]
                constraints.append(soc[i, t] == soc[i, prev_t] + charge_flow[t] * eta_c - discharge_flow[t] / eta_d)
            constraints.append(soc[i, day_slice[0]] == soc[i, day_slice[-1]])

    # 4. Define Objective Function
    print("--- Defining Objective Function ---")
    ann_inv_cost = sum(invest_units_conv[i] * conv.base_capacity * config.INVESTMENT_COSTS[conv.name] * utils.calculate_annuity_factor(config.INTEREST_RATE, config.LIFETIMES[conv.name]) for i, conv in enumerate(converters)) + \
                   sum(invest_units_stor[i] * stor.cap_base * config.INVESTMENT_COSTS[stor.name] * utils.calculate_annuity_factor(config.INTEREST_RATE, config.LIFETIMES[stor.name]) for i, stor in enumerate(storages))

    # Correctly use the config for gas price
    gas_price = typical_data['gas_price(HKD/m^3)'].values * 100 * config.GAS_PRICE_MULTIPLIER
    elec_price = typical_data['elec_price(HKD/MWh)'].values

    op_cost = sum(day_weights[d] * (cp.sum(cp.multiply(gas_flow_total[d*num_hours:(d+1)*num_hours], gas_price[d*num_hours:(d+1)*num_hours])) + cp.sum(cp.multiply(elec_flow_total[d*num_hours:(d+1)*num_hours], elec_price[d*num_hours:(d+1)*num_hours])) + cp.sum(shed_elec[d*num_hours:(d+1)*num_hours] * config.SHED_COST_PER_MWH['elec'] + shed_heat[d*num_hours:(d+1)*num_hours] * config.SHED_COST_PER_MWH['heat'] + shed_cool[d*num_hours:(d+1)*num_hours] * config.SHED_COST_PER_MWH['cool'])) for d in range(num_days))

    objective = cp.Minimize(ann_inv_cost + op_cost)

    # 5. Solve the Problem
    print("--- Solving Optimization Problem ---")
    problem = cp.Problem(objective, constraints)
    try:
        problem.solve(solver=cp.GUROBI, verbose=False)
    except cp.error.SolverError:
        print("Gurobi not found. Trying with GLPK_MI...")
        problem.solve(solver=cp.GLPK_MI, verbose=False)

    # 6. Process and Save Results
    print("\n--- Processing and Saving Results ---")
    output_dir = "results"
    scenario_name = os.path.splitext(os.path.basename(config_path))[0]

    if problem.status in ["optimal", "optimal_inaccurate"]:
        # --- Create DataFrames for CSV Export ---
        total_timesteps = num_days * num_hours
        # Energy Balance CSV
        energy_balance_df = pd.DataFrame({
            'Timestamp': typical_data.index,
            'Elec_Demand': typical_data['elec_load(MW)'].values,
            'Elec_Supply': (elec_gen).value,
            'Elec_Shed': shed_elec.value,
            'Heat_Demand': typical_data['heating_load(MW)'].values,
            'Heat_Supply': (heat_gen).value,
            'Heat_Shed': shed_heat.value,
            'Cool_Demand': typical_data['cooling_load(MW)'].values,
            'Cool_Supply': (cool_gen).value,
            'Cool_Shed': shed_cool.value,
        })
        energy_balance_df.to_csv(os.path.join(output_dir, f"{scenario_name}_energy_balance.csv"), index=False)

        # Storage SOC CSV
        storage_soc_df = pd.DataFrame(soc.value.T, columns=[s.name for s in storages])
        storage_soc_df.to_csv(os.path.join(output_dir, f"{scenario_name}_storage_soc.csv"), index=False)

        # Grid Import CSV
        grid_import_df = pd.DataFrame({
            'Timestamp': typical_data.index,
            'Gas_Import_MWh': gas_flow_total.value,
            'Elec_Import_MWh': elec_flow_total.value,
            'Gas_Price_per_MWh': gas_price,
            'Elec_Price_per_MWh': elec_price,
            'Gas_Cost_HKD': np.multiply(gas_flow_total.value, gas_price),
            'Elec_Cost_HKD': np.multiply(elec_flow_total.value, elec_price),
        })
        grid_import_df.to_csv(os.path.join(output_dir, f"{scenario_name}_grid_import.csv"), index=False)

        # --- Write Detailed Text Report ---
        report_path = os.path.join(output_dir, f"{scenario_name}_summary.txt")
        with open(report_path, 'w') as f:
            f.write(f"========= Summary for Scenario: {scenario_name} =========\n")
            f.write(f"Configuration File: {config_path}\n")
            f.write(f"Total Time: {time.time() - start_time:.2f}s\n\n")
            f.write(f"--- Cost Summary ---\n")
            f.write(f"Total Annual Cost: {problem.value:,.2f} HKD\n")
            f.write(f"  - Annualized Investment Cost: {ann_inv_cost.value:,.2f} HKD\n")
            f.write(f"  - Total Annual Operational Cost: {op_cost.value:,.2f} HKD\n\n")

            f.write("--- Investment Decisions ---\n")
            f.write("Converters:\n")
            for i, conv in enumerate(converters):
                if invest_units_conv[i].value is not None and invest_units_conv[i].value > 0.1:
                    f.write(f"  - {conv.name}: {round(invest_units_conv[i].value)} units => Capacity: {round(invest_units_conv[i].value) * conv.base_capacity:.2f} MW\n")
            f.write("\nStorages:\n")
            for i, stor in enumerate(storages):
                if invest_units_stor[i].value is not None and invest_units_stor[i].value > 0.1:
                    f.write(f"  - {stor.name}: {round(invest_units_stor[i].value)} units => Power: {round(invest_units_stor[i].value) * stor.power_base:.2f} MW, Capacity: {round(invest_units_stor[i].value) * stor.cap_base:.2f} MWh\n")
            f.write("\n")

            # Annual Energy Mix
            annual_gas_import = np.sum(gas_flow_total.value * day_weights.repeat(num_hours)) 
            annual_elec_import = np.sum(elec_flow_total.value * day_weights.repeat(num_hours))
            annual_shed_elec = np.sum(shed_elec.value * day_weights.repeat(num_hours))
            annual_shed_heat = np.sum(shed_heat.value * day_weights.repeat(num_hours))
            annual_shed_cool = np.sum(shed_cool.value * day_weights.repeat(num_hours))

            f.write("--- Annual Energy & Load Summary ---\n")
            f.write(f"Total Gas Import: {annual_gas_import:,.2f} MWh/year\n")
            f.write(f"Total Elec Import: {annual_elec_import:,.2f} MWh/year\n")
            f.write(f"Total Elec Shed: {annual_shed_elec:,.2f} MWh/year\n")
            f.write(f"Total Heat Shed: {annual_shed_heat:,.2f} MWh/year\n")
            f.write(f"Total Cool Shed: {annual_shed_cool:,.2f} MWh/year\n\n")

            # Average Prices
            if annual_gas_import > 0:
                avg_gas_price = (np.sum(gas_flow_total.value * gas_price * day_weights.repeat(num_hours))) / annual_gas_import
                f.write(f"Average Gas Price: {avg_gas_price:,.2f} HKD/MWh\n")
            if annual_elec_import > 0:
                avg_elec_price = (np.sum(elec_flow_total.value * elec_price * day_weights.repeat(num_hours))) / annual_elec_import
                f.write(f"Average Elec Price: {avg_elec_price:,.2f} HKD/MWh\n")

        # Also write constraints to a file for debugging
        constraints_path = os.path.join(output_dir, f"{scenario_name}_constraints.txt")
        with open(constraints_path, 'w') as f:
            f.write(f"========= Constraints for Scenario: {scenario_name} =========\n\n")
            for const in problem.constraints:
                f.write(str(const) + '\n')

        print(f"Detailed summary saved to {report_path}")
        print(f"Energy balance data saved to {os.path.join(output_dir, f'{scenario_name}_energy_balance.csv')}")
        print(f"Storage SOC data saved to {os.path.join(output_dir, f'{scenario_name}_storage_soc.csv')}")
        print(f"Grid import data saved to {os.path.join(output_dir, f'{scenario_name}_grid_import.csv')}")
        print(f"Constraints saved to {constraints_path}")

    else:
        print(f"Problem could not be solved. Status: {problem.status}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run MES Optimization Analysis with a specific configuration.")
    parser.add_argument('--config', type=str, default='configs/1_baseline.yaml', help='Path to the configuration YAML file')
    args = parser.parse_args()
    try:
        # The run_optimization function now handles its own config loading.
        run_optimization(args.config)
    except Exception as e:
        print(f"An error occurred: {e}")