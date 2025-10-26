# Energy Hub Planning: Analysis Report

This report analyzes the results of the energy hub optimization model under various scenarios, as defined in the project guidelines.

---

## Question 1: Impact of Load Shedding Cost

To analyze the impact of the penalty for not meeting energy demand, we ran the simulation with three different load shedding costs: 20,000 HKD/MWh (Baseline), 2,000 HKD/MWh (Mid), and 200 HKD/MWh (Low).

| Scenario              | Total Annual Cost (HKD) | Investment Cost (HKD) | Operational Cost (HKD) | Total Elec Shed (MWh/yr) | Key Investment Change from Baseline |
| --------------------- | ----------------------- | --------------------- | ---------------------- | -------------------------- | ----------------------------------- |
| **1_baseline** (20000)  | 123,136,720             | 32,007                | 123,104,713            | 0.00                       | -                                   |
| **3_shed_cost_mid** (2000) | 123,136,720             | 32,007                | 123,104,713            | 0.00                       | No Change                           |
| **2_shed_cost_low** (200)  | 73,102,935              | 8,736                 | 73,094,199             | 257,585                    | Drastically reduced all investments |

### Analysis

The results clearly demonstrate the economic trade-off between investment and reliability.

1.  **High & Medium Penalty (20,000 and 2,000 HKD/MWh):** In both the baseline and medium-cost scenarios, the penalty for shedding load is sufficiently high that the model finds it economically optimal to make significant investments (especially in electricity storage) to guarantee 100% load satisfaction. The total cost and investment strategy are identical, indicating that even a penalty of 2,000 HKD/MWh is a strong enough deterrent.

2.  **Low Penalty (200 HKD/MWh):** When the penalty is very low, the model makes a rational economic decision: it is cheaper to pay the penalty than to invest in the equipment required to meet the full demand. The investment cost drops by over 70%, and the system installs significantly less capacity, particularly for electricity storage. Consequently, it sheds a massive amount of electricity load (257,585 MWh/year) because paying the fine for this unmet demand is cheaper than building the infrastructure to serve it. This leads to a much lower total annual cost, but at the expense of system reliability.

**Conclusion:** The load shedding cost acts as a direct incentive for ensuring system reliability. A high value forces the model to build a robust system, while a low value leads to a less reliable but cheaper system that strategically fails to meet demand.

---

## Question 2: Impact of Representative Days

We analyzed the effect of using a different number of representative days (4, 8, and 12) to model the entire year.

| Scenario          | Total Annual Cost (HKD) | Investment Cost (HKD) | Solving Time (s) | Elec Storage Capacity (MWh) |
| ----------------- | ----------------------- | --------------------- | ---------------- | --------------------------- |
| **4_days_4**        | 112,782,934             | 26,634                | 1.24             | 612                         |
| **1_baseline** (8 days) | 123,136,720             | 32,007                | 3.14             | 772                         |
| **5_days_12**       | 118,202,522             | 29,800                | 5.70             | 718                         |

### Analysis

1.  **Computational Time:** There is a clear and direct relationship between the number of representative days and the computational burden. The solving time increases significantly as we move from 4 days (1.24s) to 12 days (5.70s). This is because each additional representative day adds a large number of variables (for 24 hours of operation) and constraints to the optimization problem.

2.  **Model Accuracy & Cost:** The total annual cost does not change linearly. The 8-day model yields the highest cost, suggesting it may have captured a combination of peak load and price volatility that the 4-day and 12-day clustering did not weigh as heavily. This highlights that the *quality* of the selected representative days (how well they represent the year's extremes) is as important as the *quantity*.

3.  **Investment Decisions:** The investment decisions, particularly for electricity storage, vary between scenarios. This indicates that the number of representative days directly influences the optimal system design. A model with too few days (like the 4-day model) might underestimate the need for storage to handle volatility, leading to a lower but potentially less realistic cost.

**Conclusion:** Increasing the number of representative days provides a more detailed view of the year, potentially leading to more robust investment decisions. However, this comes at the direct cost of increased computational time. The non-monotonic change in cost suggests that the clustering quality is critical, and there is a trade-off between computational burden and model fidelity.

---

## Question 4: Sensitivity Analysis on Gas Price

We investigated how the system's design changes if the price of natural gas is doubled.

| Scenario                 | Total Annual Cost (HKD) | Investment Cost (HKD) | Total Gas Import (MWh/yr) | Total Elec Import (MWh/yr) |
| ------------------------ | ----------------------- | --------------------- | ------------------------- | -------------------------- |
| **1_baseline**           | 123,136,720             | 32,007                | 0.00                      | 337,458                    |
| **6_gas_price_high**     | 123,136,720             | 32,007                | 0.00                      | 337,458                    |

### Analysis

In the baseline scenario, the optimal solution was already a fully electrified system with zero gas imports. Therefore, doubling the price of natural gas had **no impact whatsoever** on the final costs or investment decisions. The system had already determined that even at the original price, using gas-fired technologies like CHP and Gas Boilers was not economically viable compared to using electricity, especially when paired with large-scale electricity storage for price arbitrage.

**Conclusion:** This result demonstrates that, under the given cost and efficiency parameters, the system is not sensitive to increases in gas price because it has a more cost-effective, all-electric alternative. To see a change, one would need to either drastically *decrease* the gas price or *increase* the electricity price to make gas-fired generation competitive.
