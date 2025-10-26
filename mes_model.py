# Copyright (c) 2025 VerNe.
# All rights reserved.
#
# This code is for personal academic use only.
# Unauthorized use, copying, or distribution of this code is strictly prohibited.


import sympy

import config
from pymeshub.graph.builder import GraphEnergyHub
from pymeshub.components.base import Component

# --- Custom Component Definition ---
class ElectricChiller(Component):
    """
    Electric Chiller: Converts electricity to cooling with a Coefficient of Performance (COP).
    This is analogous to a HeatPump but produces cooling instead of heat.
    """
    def __init__(self, name: str, cop: sympy.Expr):
        super().__init__(name)
        self.set_parameter('cop', sympy.sympify(cop))
        self.add_input_port('elec_in', 0)
        self.add_output_port('cool_out', 1)

    def get_port_branch_matrix(self) -> sympy.Matrix:
        return sympy.Matrix([[1, 0], [0, -1]])

    def get_characteristic_matrix(self) -> sympy.Matrix:
        cop = self.get_parameter('cop')
        # Equation: cop * V_elec_in - V_cool_out = 0
        return sympy.Matrix([[cop, -1]])

def build_mes_model():
    """
    Builds the Multi-Energy System (MES) model based on the provided architecture diagram.
    
    This function uses the GraphEnergyHub to define and connect all components
    of the energy hub.
    
    Returns:
        EnergyHub: A compiled EnergyHub object containing the system matrices.
    """
    print("--- Building MES Model from Architecture Diagram ---")

    # 1. Create a GraphEnergyHub instance and register the custom component
    graph_hub = GraphEnergyHub("MES_from_diagram")
    graph_hub._component_types['ElectricChiller'] = ElectricChiller # Manual registration as per docs

    # 2. Define IO Nodes (Inputs and Loads)
    # Inputs
    graph_hub.add_io_node('Gas_Import', 'input')
    graph_hub.add_io_node('Elec_Import', 'input')
    # Loads
    graph_hub.add_io_node('Elec_Load', 'output')
    graph_hub.add_io_node('Heat_Load', 'output')
    graph_hub.add_io_node('Cooling_Load', 'output')

    # 3. Define Components with parameters from config
    # The component parameters (eta, cop) are now taken from config.py
    graph_hub.add_component('CHP_A', 'CHPBackPressure', **config.COMPONENT_PARAMS['CHP_A'])
    graph_hub.add_component('CHP_B', 'CHPBackPressure', **config.COMPONENT_PARAMS['CHP_B'])
    graph_hub.add_component('ICE', 'CHPBackPressure', **config.COMPONENT_PARAMS['ICE'])
    graph_hub.add_component('Gas_Boiler', 'Boiler', **config.COMPONENT_PARAMS['Gas_Boiler'])
    graph_hub.add_component('Elec_Boiler', 'ElectricBoiler', **config.COMPONENT_PARAMS['Elec_Boiler'])
    graph_hub.add_component('Heat_Pump_A', 'HeatPump', **config.COMPONENT_PARAMS['Heat_Pump_A'])
    graph_hub.add_component('Heat_Pump_B', 'HeatPump', **config.COMPONENT_PARAMS['Heat_Pump_B'])
    graph_hub.add_component('CERG_A', 'ElectricChiller', **config.COMPONENT_PARAMS['CERG_A'])
    graph_hub.add_component('CERG_B', 'ElectricChiller', **config.COMPONENT_PARAMS['CERG_B'])
    graph_hub.add_component('WARP', 'AbsorptionChiller', **config.COMPONENT_PARAMS['WARP'])
    graph_hub.add_component('Elec_Storage', 'Storage', **config.COMPONENT_PARAMS['Elec_Storage'])
    graph_hub.add_component('Heat_Storage', 'Storage', **config.COMPONENT_PARAMS['Heat_Storage'])
    graph_hub.add_component('Cooling_Storage', 'Storage', **config.COMPONENT_PARAMS['Cooling_Storage'])



    # 4. Connect the graph based on the four energy buses (Acyclic Logic)
    
    # --- Natural Gas Bus Connections ---
    for comp in ['CHP_A', 'CHP_B', 'ICE', 'Gas_Boiler']:
        graph_hub.connect('Gas_Import', 'out', comp, 'fuel_in')

    # --- Electricity Bus Connections (Acyclic) ---
    elec_producers = [('Elec_Import', 'out'), ('CHP_A', 'elec_out'), ('CHP_B', 'elec_out'), ('ICE', 'elec_out')]
    elec_consumers = [('Elec_Boiler', 'elec_in'), ('Heat_Pump_A', 'elec_in'), ('Heat_Pump_B', 'elec_in'),
                      ('CERG_A', 'elec_in'), ('CERG_B', 'elec_in'), ('Elec_Load', 'in')]
    elec_storage_node = 'Elec_Storage'
    # Connect producers to consumers
    for p_node, p_port in elec_producers:
        for c_node, c_port in elec_consumers:
            graph_hub.connect(p_node, p_port, c_node, c_port)
    # Connect producers to storage (charging)
    for p_node, p_port in elec_producers:
        graph_hub.connect(p_node, p_port, elec_storage_node, 'energy_in')
    # Connect storage to consumers (discharging)
    for c_node, c_port in elec_consumers:
        graph_hub.connect(elec_storage_node, 'energy_out', c_node, c_port)

    # --- Heating Bus Connections (Acyclic) ---
    heat_producers = [('Gas_Boiler', 'heat_out'), ('Elec_Boiler', 'heat_out'), 
                      ('CHP_A', 'heat_out'), ('CHP_B', 'heat_out'), ('ICE', 'heat_out'),
                      ('Heat_Pump_A', 'heat_out'), ('Heat_Pump_B', 'heat_out')]
    heat_consumers = [('WARP', 'heat_in'), ('Heat_Load', 'in')]
    heat_storage_node = 'Heat_Storage'
    # Connect producers to consumers
    for p_node, p_port in heat_producers:
        for c_node, c_port in heat_consumers:
            graph_hub.connect(p_node, p_port, c_node, c_port)
    # Connect producers to storage (charging)
    for p_node, p_port in heat_producers:
        graph_hub.connect(p_node, p_port, heat_storage_node, 'energy_in')
    # Connect storage to consumers (discharging)
    for c_node, c_port in heat_consumers:
        graph_hub.connect(heat_storage_node, 'energy_out', c_node, c_port)

    # --- Cooling Bus Connections (Acyclic) ---
    cool_producers = [('WARP', 'cool_out'), ('CERG_A', 'cool_out'), ('CERG_B', 'cool_out')]
    cool_consumers = [('Cooling_Load', 'in')]
    cool_storage_node = 'Cooling_Storage'
    # Connect producers to consumers
    for p_node, p_port in cool_producers:
        for c_node, c_port in cool_consumers:
            graph_hub.connect(p_node, p_port, c_node, c_port)
    # Connect producers to storage (charging)
    for p_node, p_port in cool_producers:
        graph_hub.connect(p_node, p_port, cool_storage_node, 'energy_in')
    # Connect storage to consumers (discharging)
    for c_node, c_port in cool_consumers:
        graph_hub.connect(cool_storage_node, 'energy_out', c_node, c_port)

    # 5. Visualize the graph topology (optional, but good for verification)
    print("Visualizing the energy hub graph...")
    # graph_hub.visualize()
    print("Graph visualization saved to 'energy_hub_graph.png'")

    # 6. Build the EnergyHub instance to get the matrices
    hub = graph_hub.build()

    # 7. Retrieve and print the system matrices
    X, Y, Z = hub.get_system_matrices()

    print("\n--- Generated Matrices from Graph Build ---")
    print(f"X Matrix (Input Incidence) shape: {X.shape}")
    # print(X)
    print(f"\nY Matrix (Output Incidence) shape: {Y.shape}")
    # print(Y)
    print(f"\nZ Matrix (System Energy Conversion) shape: {Z.shape}")
    # print(Z)
    
    print("\n--- MES Model Build Complete ---")
    return hub

if __name__ == "__main__":
    mes_hub = build_mes_model()
    # You can now use the 'mes_hub' object for further analysis or optimization.