# Energy Hub Planning: Final Analysis Report

This report analyzes the results of the energy hub optimization model under various scenarios, based on the corrected device parameters from the reference Jupyter Notebook.

---

## Overall Finding: The Dominance of the All-Electric Solution

A striking and consistent result across all scenarios is the model's complete refusal to invest in any gas-fired technology (CHP, ICE, Gas Boiler). The `Total Gas Import` remains at **0.00 MWh/year** in every case.

This indicates that under the project's given economic and technical parameters (energy prices, investment costs, and device efficiencies), an all-electric strategy is overwhelmingly the most cost-effective solution. The model consistently finds it cheaper to purchase electricity from the grid and use high-efficiency electric devices (Heat Pumps, Chillers) than to burn natural gas. The massive investment in **Electricity Storage** in most scenarios is key to this strategy, allowing the system to perform price arbitrage by charging when electricity is cheap and discharging for use or to avoid high grid prices.

---

## Question 1: Impact of Load Shedding Cost

| Scenario              | Total Annual Cost (HKD) | Investment Cost (HKD) | Operational Cost (HKD) | Total Elec Shed (MWh/yr) | Key Investment Change from Baseline |
| --------------------- | ----------------------- | --------------------- | ---------------------- | -------------------------- | ----------------------------------- |
| **1_baseline** (20000)  | 120,256,069             | 39,036                | 120,217,034            | 0.00                       | -                                   |
| **3_shed_cost_mid** (2000) | 120,256,069             | 39,036                | 120,217,034            | 0.00                       | No Change                           |
| **2_shed_cost_low** (200)  | 65,068,645              | 1,753                 | 65,066,893             | 257,585                    | Eliminated Elec_Storage investment  |

### Analysis

The trade-off between investment and reliability is clear.

1.  **High & Medium Penalty (20,000 and 2,000 HKD/MWh):** The penalty is high enough to force the model to invest in sufficient capacity (especially `Elec_Storage`) to ensure 100% load satisfaction. The identical results show that 2,000 HKD/MWh is already a strong enough deterrent.

2.  **Low Penalty (200 HKD/MWh):** The model makes a rational economic choice: it is far cheaper to pay the small penalty than to invest in the large `Elec_Storage` needed to cover peak demand or high-price periods. The investment cost plummets by over 95%. The system completely foregoes electricity storage and instead chooses to shed a massive amount of electricity, as this is the most cost-effective path.

---

## Question 2: Impact of Representative Days

| Scenario          | Total Annual Cost (HKD) | Investment Cost (HKD) | Solving Time (s) | Elec Storage Capacity (MWh) |
| ----------------- | ----------------------- | --------------------- | ---------------- | --------------------------- |
| **4_days_4**        | 109,603,645             | 32,391                | 1.25             | 632                         |
| **1_baseline** (8 days) | 120,256,069             | 39,036                | 3.29             | 756                         |
| **5_days_12**       | 116,046,683             | 38,035                | 5.74             | 740                         |

### Analysis

1.  **Computational Time:** The solving time scales directly with the number of representative days, increasing from 1.25s (4 days) to 5.74s (12 days). This is expected as more days add more variables and constraints.

2.  **Model Accuracy & Cost:** The total cost is lowest with 4 days and highest with 8 days. This non-linear relationship suggests that the quality and representativeness of the selected days are crucial. The 8-day scenario likely captures a combination of high-cost periods that the 4-day model misses, leading to a higher required investment in storage and thus a higher total cost. The 12-day model finds a slightly cheaper solution than the 8-day one, suggesting it can optimize the storage dispatch more effectively with more granular data.

**Conclusion:** More representative days provide a more detailed and likely more robust annual model, but at a direct computational cost. The results show that a model with too few days may underestimate the optimal system size and cost.

---

## Question 4: Sensitivity Analysis on Gas Price

| Scenario                 | Total Annual Cost (HKD) | Investment Cost (HKD) | Total Gas Import (MWh/yr) |
| ------------------------ | ----------------------- | --------------------- | ------------------------- |
| **1_baseline**           | 120,256,069             | 39,036                | 0.00                      |
| **6_gas_price_high**     | 120,256,069             | 39,036                | 0.00                      |

### Analysis

As expected from the baseline result, doubling the price of natural gas had **zero impact** on the outcome. The system was already fully electrified and did not import any gas. Making gas even more expensive simply reinforces the initial decision that it is not an economically viable energy source for this system under the current parameters.

**Conclusion:** The model is completely insensitive to gas price *increases* because the all-electric solution is already significantly cheaper. A sensitivity analysis with a drastically *reduced* gas price would be required to find the break-even point where gas-fired technologies might become part of the optimal solution.
